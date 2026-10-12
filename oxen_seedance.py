"""Oxen Seedance drafts using reviewed Genjutsu media, never automatic paid retries."""
import json
import math
import re
import shutil
import time
import uuid
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlparse

import av
import requests
from PIL import Image

from audio_workflow import finish_preview
from config import credential
from lec_seedance import media_seconds, plan_hash, align_result
from mask_review import require_approved
from replicate_seedance import build_prompt
from oxen_media import upload_file, MediaLinkError
from seedance_media import upload_video

API = 'https://hub.oxen.ai/api'
MODEL = 'bytedance-seedance-2-5-reference-to-video'
# Published model JSON, October 11, 2026. Estimate only; refreshed before submission.
RATE_480 = 0.111


def headers():
    return {'Authorization': 'Bearer ' + credential('OXEN_API_KEY')}


def upload_copy(source,folder,index):
    record=folder/('input-'+str(index)+'.json')
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    saved=json.loads(record.read_text()) if record.exists() else {}
    target=folder/saved.get('upload','missing')
    if saved.get('source_sha256')==digest and target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest()==saved.get('upload_sha256'):
        return target
    target=upload_video(source,folder,index)
    record.write_text(json.dumps({'source_sha256':digest,'upload':target.name,
                                 'upload_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))
    return target


def plan(folder, prompt, reference, second=None):
    folder = Path(folder)
    prepared = folder / 'seedance-input.mp4'
    manifest = json.loads((folder / 'audio-manifest.json').read_text())
    if manifest.get('pitch_semitones') != 3:
        raise ValueError('The prepared input must contain isolated vocals pitched +3.')
    videos, images = [prepared], []
    refs = [Path(reference)] + ([Path(second)] if second else [])
    video_identity = refs[0].suffix.lower() in {'.mp4', '.mov', '.webm'}
    for path in refs:
        if path.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp'}:
            with Image.open(path) as image:
                image.verify()
            images.append(path)
        elif path.suffix.lower() in {'.mp4', '.mov', '.webm'}:
            videos.append(path)
        else:
            raise ValueError('Use a JPEG, PNG, WebP, MP4, MOV or WebM identity reference.')
    if second and video_identity is False and Path(second).suffix.lower() in {'.mp4', '.mov', '.webm'}:
        raise ValueError('The optional second identity reference must be an image.')
    for path in videos:
        with av.open(str(path)) as container:
            if not container.streams.video:
                raise ValueError('A reference video has no video stream.')
            if path == prepared and not container.streams.audio:
                raise ValueError('The prepared video is missing its embedded pitched vocals.')
        if not 2 <= media_seconds(path) <= 30:
            raise ValueError('Each reference video must be 2–30 seconds.')
    seconds = media_seconds(prepared)
    if seconds < 4 or sum(media_seconds(path) for path in videos) > 30.05:
        raise ValueError('The prepared clip must be 4–30 seconds; combined videos must stay within 30 seconds.')
    actual = re.sub(r'\[(Video|Image|Audio)(\d+)\]', r'@\1\2',
                    build_prompt(folder, prompt, video_identity, bool(second)))
    payload = {'model': MODEL, 'prompt': actual, 'omni_reference_task_type': 'auto' if video_identity else 'edit',
               'generate_audio': False, 'aspect_ratio': 'adaptive', 'duration': 'auto',
               'resolution': '480p', 'draft': True, 'output_format': 'mp4', 'watermark': False}
    return payload, videos, images


def preview(folder, prompt, reference, second=None):
    payload, videos, images = plan(folder, prompt, reference, second)
    seconds = media_seconds(videos[0])
    return {'prompt': payload['prompt'], 'user_prompt': prompt, 'duration': round(seconds, 3),
            'aspect_ratio': payload['aspect_ratio'], 'resolution': '480p', 'draft': True,
            'generate_audio': payload['generate_audio'],
            'price_usd': round(math.ceil(seconds) * RATE_480, 2), 'rate_usd': RATE_480,
            'billing': 'per_video_output_second', 'hash': plan_hash(payload, videos, images),
            'local_videos': [p.name for p in videos], 'local_images': [p.name for p in images]}


def preflight():
    """Read-only authentication and price check, before uploading any media."""
    response = requests.get(API + '/ai/queue', headers=headers(), timeout=30)
    if response.status_code in {401, 403}:
        raise ValueError('Oxen did not accept this API key. Check your Oxen account; no video submitted.')
    response.raise_for_status()
    response = requests.get(API + '/ai/models/' + MODEL, headers=headers(), timeout=30)
    response.raise_for_status()
    data = response.json()
    pricing = data.get('pricing', {})
    rate = pricing.get('cost_per_second_by_resolution', {}).get('480p')
    if not data.get('can_run_inference') or pricing.get('method') != 'per_video_output_second' or not isinstance(rate, (float, int)):
        raise ValueError('Oxen model availability or pricing changed. Review its current model page before submission.')
    if rate > RATE_480 * 1.01:
        raise ValueError('Oxen increased the 480p price. Review the updated price before submission.')
    return float(rate)


def enqueue(folder, payload, response_name):
    response = requests.post(API + '/ai/queue', headers=headers(), json=payload, timeout=60)
    if not response.ok:
        (folder / 'submission-error.json').write_text(json.dumps({'status': response.status_code, 'body': response.text}))
        raise ValueError(f'Oxen submission returned HTTP {response.status_code}. Inspect the saved error; no automatic retry.')
    data = response.json()
    items = data.get('generations', [])
    ident = items[0].get('generation_id') if len(items) == 1 else None
    saved = {**data, 'provider': 'oxen', 'requestId': ident, 'id': ident,
             'status': items[0].get('status') if len(items) == 1 else 'unknown'}
    (folder / response_name).write_text(json.dumps(saved, indent=2))
    if not ident:
        raise ValueError('Oxen returned no unique generation ID. Check its console before retrying.')
    (folder / 'submission-intent.json').write_text(json.dumps({'provider': 'oxen', 'state': 'submitted', 'id': ident}))
    return ident


def submit(folder, prompt, reference, second=None, status=print):
    folder = Path(folder)
    require_approved(folder)
    marker = folder / 'submission-intent.json'
    if marker.exists() or (folder / 'seedance-response.json').exists():
        raise ValueError('This job was already attempted. Resume its saved Oxen generation; do not submit again.')
    payload, videos, images = plan(folder, prompt, reference, second)
    reviewed = folder / 'oxen-plan-review.json'
    if not reviewed.exists() or json.loads(reviewed.read_text()).get('hash') != plan_hash(payload, videos, images):
        raise ValueError('Review the exact Oxen prompt and price first. No uploads or generation submitted.')
    rate = preflight()
    local_videos, local_images = ['seedance-input.mp4'], []
    for index, path in enumerate(videos[1:] + images, 1):
        target = folder / ('oxen-reference-' + str(index) + path.suffix.lower())
        if target.resolve() != path.resolve():
            shutil.copy2(path, target)
        (local_videos if path in videos[1:] else local_images).append(target.name)
    generation = {'provider': 'oxen', 'model': MODEL, 'resolution': '480p', 'draft': True,
                  'mode': payload['omni_reference_task_type'], 'prompt': payload['prompt'], 'user_prompt': prompt,
                  'generate_audio': payload['generate_audio'],
                  'duration': media_seconds(videos[0]), 'rate_usd': rate,
                  'local_videos': local_videos, 'local_images': local_images, 'video': 'seedance-result.mp4'}
    try:
        with marker.open('x') as intent:
            json.dump({'provider': 'oxen', 'state': 'uploading'}, intent)
    except FileExistsError:
        raise ValueError('Another Oxen submission already started.')
    (folder / 'generation.json').write_text(json.dumps(generation, indent=2))
    try:
        status('Uploading reviewed video and portrait to private Oxen storage; verifying signed media downloads')
        upload_folder = folder / 'oxen-upload'
        upload_folder.mkdir(exist_ok=True)
        upload_videos = [upload_copy(folder / name, upload_folder, index)
                         for index, name in enumerate(local_videos, 1)]
        generation['upload_videos'] = [str(path.relative_to(folder)) for path in upload_videos]
        (folder / 'generation.json').write_text(json.dumps(generation, indent=2))
        # All references show people/characters, so keep face inputs together and preserve @Video1 ordering.
        payload['input_face_videos'] = [upload_file(path) for path in upload_videos]
        payload['input_face_images'] = [upload_file(folder / name) for name in local_images]
        (folder / 'seedance-request.json').write_text(json.dumps(payload, indent=2))
        marker.write_text(json.dumps({'provider': 'oxen', 'state': 'submitting'}))
        status('Submitting one Seedance 2.5 480p draft to Oxen')
        ident = enqueue(folder, payload, 'seedance-response.json')
        generation['request_id'] = ident
        (folder / 'generation.json').write_text(json.dumps(generation, indent=2))
        status('Oxen draft accepted: ' + ident)
        return ident
    except MediaLinkError as exc:
        marker.write_text(json.dumps({'provider': 'oxen', 'state': 'not_submitted', 'reason': str(exc)}))
        raise
    except requests.RequestException as exc:
        if json.loads(marker.read_text()).get('state') == 'uploading':
            reason='Media upload stopped before generation submission. Your reviewed input is saved.'
            marker.write_text(json.dumps({'provider':'oxen','state':'not_submitted','reason':reason}))
            raise RuntimeError(reason) from exc
        raise RuntimeError('Oxen request needs inspection. Saved intent prevents duplicate generation charges; do not resubmit blindly.') from exc


def recover_upload(folder):
    """Explicit recovery of a proven non-submission; preserve its entire audit."""
    folder=Path(folder)
    marker=folder/'submission-intent.json'
    intent=json.loads(marker.read_text())
    generation=json.loads((folder/'generation.json').read_text())
    if intent.get('state')!='not_submitted' or intent.get('provider')!='oxen' or generation.get('request_id'):
        raise ValueError('Only confirmed Oxen upload failures can be recovered. Resume any saved generation instead.')
    if any((folder/name).exists() for name in ['seedance-request.json','seedance-response.json','submission-error.json','provider-status.json']):
        raise ValueError('A generation may already have been sent. Do not submit another request.')
    require_approved(folder)
    references=[folder/name for name in generation['local_videos'][1:]+generation['local_images']]
    if not 1<=len(references)<=2 or any(path.parent.resolve()!=folder.resolve() for path in references):
        raise ValueError('Saved identity references need inspection.')
    prompt=generation['user_prompt']
    payload,videos,images=plan(folder,prompt,*references)
    if json.loads((folder/'oxen-plan-review.json').read_text()).get('hash')!=plan_hash(payload,videos,images):
        raise ValueError('The saved request changed. Review its prompt and references first.')
    audit=folder/'upload-attempts'/uuid.uuid4().hex
    audit.mkdir(parents=True)
    for name in ['generation.json','status.json']:
        if (folder/name).exists():shutil.copy2(folder/name,audit/name)
    marker.replace(audit/'submission-intent.json')
    return prompt,references


def wait_and_finish(folder, ident, status=print):
    folder = Path(folder)
    for _ in range(720):
        response = requests.get(API + '/ai/queue/' + quote(ident, safe=''), headers=headers(), timeout=30)
        if response.status_code == 429 or response.status_code >= 500:
            status('Oxen status check delayed; checking the same saved generation again')
            time.sleep(15)
            continue
        response.raise_for_status()
        data = response.json()
        (folder / 'provider-status.json').write_text(json.dumps(data, indent=2))
        phase = data.get('status')
        status('Oxen · ' + str(phase or 'unknown') + ' · generation ' + ident)
        if phase in {'failed', 'cancelled', 'canceled'}:
            raise RuntimeError('Oxen generation ' + phase + ': ' + str(data.get('error_message') or ''))
        if phase == 'succeeded':
            videos = data.get('videos') or []
            item = videos[0] if len(videos) == 1 else {}
            url = item.get('url') or data.get('result_url')
            if not isinstance(url, str) or not url.startswith('https://'):
                raise ValueError('Oxen succeeded but its downloadable video URL is missing.')
            generation = json.loads((folder / 'generation.json').read_text())
            for key in ['draft_task_id', 'draft_expires_at']:
                if item.get(key):
                    generation[key] = item[key]
            (folder / 'generation.json').write_text(json.dumps(generation, indent=2))
            status('Oxen finished; downloading video and restoring the complete original soundtrack')
            # A signed output URL needs no account credential; never leak the key to another host.
            with requests.get(url, stream=True, timeout=180) as media:
                media.raise_for_status()
                temporary = folder / 'seedance-result.pending'
                with temporary.open('wb') as out:
                    for chunk in media.iter_content(1024 * 1024):
                        out.write(chunk)
                temporary.replace(folder / 'seedance-result.mp4')
            finish_preview(align_result(folder), folder)
            return
        if phase not in {'queued', 'processing'}:
            raise RuntimeError('Oxen reports an unknown state. Inspect the saved generation; do not submit again.')
        time.sleep(15)
    raise TimeoutError('Oxen is still pending. Resume its saved generation ID; no new request was submitted.')


def submit_hd(folder):
    folder = Path(folder)
    require_approved(folder)
    generation = json.loads((folder / 'generation.json').read_text())
    if not (folder / 'final-preview.mp4').exists() or not generation.get('draft_task_id'):
        raise ValueError('A completed Oxen draft with its draft task ID is required.')
    expires = generation.get('draft_expires_at')
    if not expires or datetime.fromisoformat(expires.replace('Z', '+00:00')) <= datetime.now(timezone.utc):
        raise ValueError('This Oxen draft expired or has no verified expiry. No final submitted.')
    hd = folder / 'hd'
    hd.mkdir(exist_ok=True)
    if (hd / 'submission-intent.json').exists() or (hd / 'response.json').exists():
        raise ValueError('The final was already attempted. Resume its saved generation.')
    payload = {'model': MODEL, 'draft_task_id': generation['draft_task_id']}
    credential('OXEN_API_KEY')
    with (hd / 'submission-intent.json').open('x') as out:
        json.dump({'provider': 'oxen', 'state': 'submitting'}, out)
    shutil.copy2(folder / 'upload.mp4', hd / 'upload.mp4')
    (hd / 'request.json').write_text(json.dumps(payload, indent=2))
    (hd / 'generation.json').write_text(json.dumps({**generation, 'resolution': '1080p', 'draft': False}, indent=2))
    ident = enqueue(hd, payload, 'response.json')
    record = json.loads((hd / 'generation.json').read_text())
    record['request_id'] = ident
    (hd / 'generation.json').write_text(json.dumps(record, indent=2))
    return ident
