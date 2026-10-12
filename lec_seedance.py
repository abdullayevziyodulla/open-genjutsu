"""Raw Lec Seedance adapter. No paid request is retried automatically."""
import hashlib
import json
import math
import mimetypes
import re
import shutil
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlparse

import av
import requests

from audio_workflow import finish_preview
from config import credential
from mask_review import require_approved
from replicate_seedance import build_prompt

API = 'https://api.paipu.net'
MODEL = 'lec-mj-seedance-2-5-bd-720p'


def headers():
    return {'Authorization': 'Bearer ' + credential('LEC_API_KEY')}


def media_seconds(path):
    with av.open(str(path)) as container:
        stream = container.streams.video[0]
        return float(stream.duration * stream.time_base) if stream.duration else float(container.duration / av.time_base)


def validate_media(path):
    path = Path(path)
    mime = mimetypes.guess_type(path.name)[0] or ''
    allowed = {'image/jpeg', 'image/png', 'image/webp', 'video/mp4', 'video/webm'}
    if mime not in allowed:
        raise ValueError('Lec accepts JPEG, PNG, WebP, MP4 or WebM references. Convert MOV before using it.')
    limit = (5 if mime.startswith('image/') else 30) * 1024 * 1024
    if path.stat().st_size > limit:
        raise ValueError('Lec upload limit: 5 MiB per image, 30 MiB per video. No paid request submitted.')
    return mime


def upload_file(folder, path):
    """Use Lec's private signed storage, with a saved per-asset idempotency key."""
    path = Path(path)
    mime = validate_media(path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    record = folder / ('lec-upload-' + digest + '.json')
    if record.exists():
        saved = json.loads(record.read_text())
        if saved.get('url') and datetime.fromisoformat(saved['expires_at'].replace('Z', '+00:00')) > datetime.now(timezone.utc):
            return saved['url']
        ident = saved['idempotency_key'] if not saved.get('url') else uuid.uuid4().hex
    else:
        ident = uuid.uuid4().hex
    record.write_text(json.dumps({'idempotency_key': ident, 'sha256': digest}))
    with path.open('rb') as source:
        response = requests.post(API + '/v1/media/temporary-assets',
            headers={**headers(), 'Idempotency-Key': ident},
            files={'file': (path.name, source, mime)}, timeout=120)
    response.raise_for_status()
    data = response.json()['data']
    if not data.get('url', '').startswith('https://') or not data.get('expires_at'):
        raise ValueError('Lec upload did not return a signed HTTPS URL and expiry.')
    record.write_text(json.dumps({**data, 'idempotency_key': ident, 'sha256': digest}, indent=2))
    return data['url']


def plan(folder, prompt, reference, second=None):
    folder = Path(folder)
    prepared = folder / 'seedance-input.mp4'
    if not prepared.exists() or not (folder / 'audio-manifest.json').exists():
        raise ValueError('Prepare and review the depth/mesh video with embedded vocals first.')
    refs = [Path(reference)] + ([Path(second)] if second else [])
    video_identity = validate_media(refs[0]).startswith('video/')
    videos = [prepared] + (refs[:1] if video_identity else [])
    images = refs[1:] if video_identity else refs
    for path in videos + images:
        validate_media(path)
    if sum(media_seconds(path) for path in videos) > 30.05:
        raise ValueError('Keep combined video references within 30 seconds.')
    seconds = media_seconds(prepared)
    if not 3.95 <= seconds <= 30:
        raise ValueError('Lec requires a source between 4 and 30 seconds.')
    with av.open(str(prepared)) as container:
        stream = container.streams.video[0]
        ratio = stream.width / stream.height
    ratios = {'16:9': 16/9, '9:16': 9/16, '1:1': 1}
    aspect = min(ratios, key=lambda value: abs(ratios[value] - ratio))
    if abs(ratios[aspect] - ratio) > 0.03:
        raise ValueError('This Lec route supports 16:9, 9:16 and 1:1. Prepare a matching frame before submission.')
    actual = build_prompt(folder, prompt, video_identity, bool(second))
    actual = re.sub(r'\[(Video|Image|Audio)(\d+)\]', r'@\1\2', actual)
    duration=max(4, math.ceil(seconds))
    if duration-seconds>0.01:
        actual=actual.replace('exact source duration. Do not extend or shorten the clip.',
            f'source action timing at normal speed over its first {seconds:.3f} seconds. '
            f'The requested output is {duration} seconds; hold the final pose only after the source action ends. '
            'Do not slow down, omit or invent any source action. The extra trailing hold will be trimmed locally.')
    return {'model': MODEL, 'prompt': actual, 'duration': duration,
            'aspect_ratio': aspect}, videos, images


def submit(folder, prompt, reference, second=None, status=print):
    folder = Path(folder)
    require_approved(folder)
    credential('LEC_API_KEY')
    marker = folder / 'submission-intent.json'
    if marker.exists() or (folder / 'seedance-response.json').exists():
        raise ValueError('This job was already attempted. Resume its saved Lec task; do not submit again.')
    payload, videos, images = plan(folder, prompt, reference, second)
    approval = folder / 'lec-plan-review.json'
    if not approval.exists() or json.loads(approval.read_text()).get('hash') != plan_hash(payload, videos, images):
        raise ValueError('Review the exact Lec prompt and cost in the app before submitting. No paid uploads started.')
    local_images, local_videos = [], ['seedance-input.mp4']
    for index, path in enumerate(videos[1:] + images, 1):
        target = folder / ('lec-reference-' + str(index) + path.suffix.lower())
        if target.resolve() != path.resolve():
            shutil.copy2(path, target)
        (local_videos if path in videos[1:] else local_images).append(target.name)
    generation = {'provider': 'lec', 'model': MODEL, 'mode': 'reference', 'resolution': '720p',
                  'prompt': payload['prompt'], 'user_prompt': prompt, 'duration': payload['duration'],
                  'local_videos': local_videos, 'local_images': local_images,
                  'video': 'seedance-result.mp4', 'price_cny': 4.5,
                  'upload_price_usd': 0.05 * len(videos) + 0.01 * len(images)}
    # Claim ownership before even the billed media uploads.
    try:
        with marker.open('x') as intent:
            json.dump({'provider': 'lec', 'model': MODEL, 'state': 'uploading'}, intent)
    except FileExistsError:
        raise ValueError('Another Lec submission already started.')
    (folder / 'generation.json').write_text(json.dumps(generation, indent=2))
    try:
        status('Uploading prepared depth video and identity references to Lec private storage')
        payload['videos'] = [upload_file(folder, folder / name) for name in local_videos]
        payload['images'] = [upload_file(folder, folder / name) for name in local_images]
        payload['audios'] = []  # Pitched vocals are embedded in Video1.
        (folder / 'seedance-request.json').write_text(json.dumps(payload, indent=2))
        marker.write_text(json.dumps({'provider': 'lec', 'model': MODEL, 'state': 'submitting'}))
        status('Submitting raw Seedance 2.5 to Lec · 720p · ¥4.50 per request')
        response = requests.post(API + '/v1/videos', headers=headers(), json=payload, timeout=90)
        if not response.ok:
            (folder / 'submission-error.json').write_text(json.dumps({'status': response.status_code, 'body': response.text}))
            raise ValueError(f'Lec submission returned HTTP {response.status_code}. Inspect the saved error; no automatic retry.')
        data = response.json()
        ident = data.get('id') or data.get('task_id')
        saved = {**data, 'provider': 'lec', 'requestId': ident}
        (folder / 'seedance-response.json').write_text(json.dumps(saved, indent=2))
        if not ident:
            raise ValueError('Lec did not return a task ID. Submission outcome is uncertain; check its console before retrying.')
        generation['request_id'] = ident
        (folder / 'generation.json').write_text(json.dumps(generation, indent=2))
        marker.write_text(json.dumps({'provider': 'lec', 'state': 'submitted', 'id': ident}))
        status('Lec task accepted: ' + ident)
        return ident
    except requests.RequestException as exc:
        raise RuntimeError('Lec request outcome needs inspection. Saved intent prevents duplicate charges; do not submit again blindly.') from exc


def align_result(folder):
    """Drop only a subsecond generated tail required by integer output duration."""
    raw = folder / 'seedance-result.mp4'
    source_seconds, result_seconds = media_seconds(folder / 'upload.mp4'), media_seconds(raw)
    excess = result_seconds - source_seconds
    if excess <= 0.25:
        return raw
    if excess > 1.05:
        raise ValueError('Generated video is over one second longer than the source. Inspect it before alignment.')
    from fractions import Fraction
    target = folder / 'seedance-duration-aligned.mp4'
    with av.open(str(raw)) as inp, av.open(str(target), 'w') as out:
        video = inp.streams.video[0]
        rate = video.average_rate or Fraction(24, 1)
        stream = out.add_stream('libx264', rate=rate)
        stream.width, stream.height, stream.pix_fmt = video.width, video.height, 'yuv420p'
        stream.options = {'crf': '18'}
        count = round(source_seconds * float(rate))
        for index, frame in enumerate(inp.decode(video=0)):
            if index >= count:
                break
            frame.pts, frame.time_base = index, 1 / rate
            for packet in stream.encode(frame):
                out.mux(packet)
        for packet in stream.encode():
            out.mux(packet)
    (folder / 'duration-adjustment.json').write_text(json.dumps({
        'method': 'trim generated tail for integer-duration rounding', 'seconds': excess,
        'original_audio': 'unchanged', 'speed': 'unchanged'}, indent=2))
    return target


def plan_hash(payload, videos, images):
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode())
    for path in videos + images:
        digest.update(Path(path).read_bytes())
    return digest.hexdigest()


def wait_and_finish(folder, ident, status=print):
    folder = Path(folder)
    endpoint = API + '/v1/videos/' + quote(ident, safe='')
    for _ in range(720):
        response = requests.get(endpoint, headers=headers(), timeout=30)
        if response.status_code == 429 or response.status_code >= 500:
            try:
                delay = min(60, max(5, int(response.headers.get('Retry-After', '10'))))
            except ValueError:
                delay = 10
            status('Lec status check delayed · saved task will be checked again')
            time.sleep(delay)
            continue
        response.raise_for_status()
        data = response.json()
        (folder / 'provider-status.json').write_text(json.dumps(data, indent=2))
        phase = data.get('status')
        status('Lec · ' + str(data.get('phase') or phase or 'unknown') +
               (' · ' + str(data['progress']) + '%' if data.get('progress') is not None else ''))
        if phase == 'failed':
            raise RuntimeError('Lec generation failed: ' + json.dumps(data.get('error') or {}, ensure_ascii=False))
        if phase == 'unknown':
            raise RuntimeError('Lec reports an unknown state. Inspect the saved task ID before retrying; no new request was submitted.')
        if phase == 'completed':
            url = data.get('url') or data.get('result_url') or (data.get('metadata') or {}).get('url')
            if not isinstance(url, str) or not url.startswith('https://'):
                raise ValueError('Lec completed the task but did not return a downloadable HTTPS result.')
            # Never send the Lec key to an upstream download host.
            auth = headers() if urlparse(url).hostname == 'api.paipu.net' else {}
            media = requests.get(url, headers=auth, timeout=180)
            media.raise_for_status()
            (folder / 'seedance-result.mp4').write_bytes(media.content)
            status('Restoring the complete original soundtrack · generated audio discarded')
            finish_preview(align_result(folder), folder)
            return
        time.sleep(5)
    raise TimeoutError('Lec task is still pending. Resume the saved task ID; no new generation was submitted.')


def prepare_job(source):
    """Copy existing reviewed preparation to a new Lec job without rerunning inference."""
    source = Path(source)
    require_approved(source)
    target = source.parent / uuid.uuid4().hex
    excluded = {'seedance-request.json', 'seedance-response.json', 'generation.json', 'provider-status.json',
                'status.json', 'submission-intent.json', 'submission-error.json', 'seedance-result.mp4',
                'final-preview.mp4', 'seedance-duration-aligned.mp4', 'duration-adjustment.json', 'hd',
                'retry-preview.json', 'retry-source.json', 'revision-preview.json', 'revision-source.json',
                'preferred-engine.json', 'lec-plan-review.json', 'lec-request-preview.json'}
    shutil.copytree(source, target, ignore=lambda path, names: {name for name in names
        if name in excluded or name.startswith('lec-upload-')})
    require_approved(target)
    (target / 'preferred-engine.json').write_text(json.dumps({'engine': 'seedance'}))
    (target / 'provider-source.json').write_text(json.dumps({'provider': 'lec', 'source_job': source.name}))
    (target / 'status.json').write_text(json.dumps({'id': target.name, 'state': 'done',
        'status': 'Existing reviewed preparation retained · add your Lec key to generate 720p.'}))
    return target
