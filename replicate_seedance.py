"""Replicate Seedance 2.5: 480p preview, separately approved 720p regeneration."""
import json
import hashlib
import mimetypes
import re
import shutil
import time
from pathlib import Path
from urllib.parse import urlparse

import av
import requests

from config import credential
from mask_review import require_approved, is_mesh
from audio_workflow import finish_preview
from seedance_media import upload_video

MODEL = 'bytedance/seedance-2.5'
API = 'https://api.replicate.com/v1'


def headers():
    return {'Authorization': 'Bearer ' + credential('REPLICATE_API_TOKEN')}


def upload_file(path):
    path=Path(path)
    content_type=mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
    with path.open('rb') as source:
        response = requests.post(API + '/files', headers=headers(),
                                 files={'content': (path.name, source, content_type)}, timeout=120)
    response.raise_for_status()
    return response.json()['urls']['get']


def validate_duration(paths):
    total = 0
    for path in paths:
        with av.open(str(path)) as video:
            stream = video.streams.video[0]
            seconds = (float(stream.duration * stream.time_base) if stream.duration
                       else float(video.duration / av.time_base))
        total += seconds
    if total > 30.05:
        raise ValueError('Seedance 2.5 allows at most 30 seconds of video references combined. Shorten the source or identity reference.')


def build_prompt(folder, prompt, video_identity=False, second=False):
    prompt = re.sub(r'@(?:Video|Image|Audio)(\d+)', lambda m: '[' + m[0][1:] + ']', prompt)
    prompt = prompt.replace('[Audio1]', 'the audio embedded in [Video1]')
    description = 'colored-depth composite'
    if is_mesh(folder):
        mode = json.loads((folder / 'workflow-mode.json').read_text())['mode']
        description = 'depth composite with face mesh overlay' if mode == 'depth_mesh' else 'original video with face mesh overlay'
    guidance = ('[Video2] supplies only the replacement visual identity; ignore its audio and motion.'
                if video_identity else '[Image1] supplies the replacement character identity.')
    if second:
        guidance += ' ' + ('[Image1]' if video_identity else '[Image2]') + ' supplies the second character identity.'
    return (prompt + '\nEdit [Video1], the ' + description + ' with isolated vocals pitched +3 semitones. '
            'Use only its embedded audio for dialogue, performance and lip synchronization. ' + guidance +
            ' Remove all depth colors and face mesh lines. Replace the complete selected identity including hair. '
            'Preserve the background, camera movement, framing, action order and exact source duration. Do not extend or shorten the clip.')


def queue(folder, payload, response_name, model=MODEL):
    """Persist an intent before POST so ambiguous responses cannot cause duplicate charges."""
    marker = folder / 'submission-intent.json'
    if marker.exists() or (folder / response_name).exists():
        raise ValueError('Submission already attempted. Inspect the saved prediction or Replicate dashboard before retrying; automatic resubmission is blocked.')
    (folder / ('request.json' if response_name == 'response.json' else 'seedance-request.json')).write_text(json.dumps(payload, indent=2))
    try:
        with marker.open('x') as intent:
            json.dump({'provider': 'replicate', 'model': model, 'state': 'submitting'}, intent)
    except FileExistsError:
        raise ValueError('Another submission already started. Inspect its saved prediction before retrying.')
    try:
        response = requests.post(API + '/models/' + model + '/predictions', headers=headers(), json=payload, timeout=90)
        if not response.ok:
            (folder / 'submission-error.json').write_text(json.dumps({'status': response.status_code, 'body': response.text}))
            raise ValueError(f'Replicate rejected submission (HTTP {response.status_code}). See submission-error.json.')
        data = response.json()
        # Preserve the repository's collector/CLI field while retaining the native prediction.
        data.update(provider='replicate', requestId=data.get('id'))
        (folder / response_name).write_text(json.dumps(data, indent=2))
        if not data.get('id'):
            raise ValueError('Replicate returned no prediction ID. Inspect the saved response before retrying.')
        marker.write_text(json.dumps({'provider': 'replicate', 'state': 'submitted', 'id': data['id']}))
        return data['id']
    except requests.RequestException as exc:
        raise RuntimeError('Replicate submission outcome is uncertain. Check your dashboard before another paid request; submission intent is saved.') from exc


def submit(folder, prompt, reference, second=None, status=print, prompt_is_final=False):
    folder = Path(folder)
    require_approved(folder)
    if (folder / 'seedance-response.json').exists() or (folder / 'submission-intent.json').exists():
        raise ValueError('This job has already been submitted or attempted. Resume or inspect its saved request.')
    credential('REPLICATE_API_TOKEN')
    if not (folder / 'audio-manifest.json').exists() or not (folder / 'seedance-input.mp4').exists():
        raise ValueError('Prepare and review the video with embedded pitched vocals before submission.')
    reference = Path(reference).resolve()
    second = Path(second).resolve() if second else None
    # Store local references so the approved 720p run can upload fresh files later.
    references = []
    for index, path in enumerate([reference] + ([second] if second else []), 1):
        local = folder / ('replicate-reference-' + str(index) + path.suffix.lower())
        if path != local.resolve():
            shutil.copy2(path, local)
        references.append(local)
    video_identity = reference.suffix.lower() in ['.mp4', '.mov', '.webm']
    videos = [folder / 'seedance-input.mp4'] + (references[:1] if video_identity else [])
    images = references[1:] if video_identity else references
    actual_prompt = prompt if prompt_is_final else build_prompt(folder, prompt, video_identity, bool(second))
    revision_path=folder/'revision-source.json'
    if revision_path.exists():
        revision=json.loads(revision_path.read_text())
        old_generation=revision['generation']
        old_refs=old_generation['local_videos'][1:]+old_generation.get('local_images',[])
        original_folder=folder.parent/revision['id']
        old_hashes=[hashlib.sha256((original_folder/name).read_bytes()).hexdigest() for name in old_refs]
        new_hashes=[hashlib.sha256(path.read_bytes()).hexdigest() for path in references]
        if actual_prompt.strip()==old_generation['prompt'].strip() and new_hashes==old_hashes:
            raise ValueError('This is the same input Replicate already rejected. Change the character reference or prompt before submitting again.')
    validate_duration(videos)
    status('Checking video references and correcting upload dimensions')
    upload_videos = [upload_video(p, folder, index) for index,p in enumerate(videos,1)]
    status('Uploading prepared video and character references to Replicate')
    payload = {'input': {'prompt': actual_prompt, 'reference_videos': [upload_file(p) for p in upload_videos],
                         'reference_images': [upload_file(p) for p in images], 'duration': -1,
                         'aspect_ratio': 'adaptive', 'resolution': '480p', 'output_format': 'mp4',
                         'generate_audio': True}}
    ident = queue(folder, payload, 'seedance-response.json')
    (folder / 'generation.json').write_text(json.dumps({'request_id': ident, 'provider': 'replicate',
        'model': MODEL, 'mode': 'multi_reference' if video_identity else 'edit', 'resolution': '480p',
        'prompt': actual_prompt, 'user_prompt':prompt.split('\nEdit [Video1], the ',1)[0] if prompt_is_final else prompt,
        'video': 'seedance-result.mp4',
        'local_videos': [p.name for p in videos], 'local_images': [p.name for p in images]}, indent=2))
    status('Replicate 480p preview submitted: ' + ident)
    return ident


def wait_and_finish(folder, ident, status=print):
    folder = Path(folder)
    for _ in range(360):
        response = requests.get(API + '/predictions/' + ident, headers=headers(), timeout=30)
        response.raise_for_status()
        data = response.json()
        (folder / 'provider-status.json').write_text(json.dumps(data, indent=2))
        phase=data.get('status')
        if phase=='starting':status('Replicate accepted the request · waiting to start generation')
        elif phase=='processing':status('Generating video on Replicate')
        if data.get('status') == 'succeeded':
            status('Generation finished · downloading the video')
            output = data.get('output')
            if isinstance(output, list) and len(output) == 1:
                output = output[0]
            if not isinstance(output, str) or not output.startswith('https://'):
                raise ValueError('Prediction succeeded but its video URL is missing or expired. Inspect the saved provider status.')
            host = urlparse(output).hostname or ''
            auth = headers() if host == 'replicate.delivery' or host.endswith('.replicate.delivery') else {}
            response = requests.get(output, headers=auth, timeout=180)
            response.raise_for_status()
            (folder / 'seedance-result.mp4').write_bytes(response.content)
            status('Restoring the entire original source audio')
            finish_preview(folder / 'seedance-result.mp4', folder)
            return
        if data.get('status') in ['failed', 'canceled']:
            raise RuntimeError('Replicate prediction ' + data['status'] + ': ' + str(data.get('error') or ''))
        time.sleep(10)
    raise TimeoutError('Prediction still pending. Resume the saved ID; do not submit again.')


def submit_hd(folder):
    """A new 720p prediction, not a continuation or an upscale of the preview."""
    folder = Path(folder)
    generation_path=folder/'generation.json'
    if generation_path.exists() and json.loads(generation_path.read_text()).get('model')=='wan-video/wan-2.2-animate-replace':
        from wan_bridge import submit_hd as wan_hd
        return wan_hd(folder)
    require_approved(folder)
    if not (folder / 'final-preview.mp4').exists():
        raise ValueError('Complete and review the 480p preview first.')
    hd = folder / 'hd'
    hd.mkdir(exist_ok=True)
    if (hd / 'response.json').exists() or (hd / 'submission-intent.json').exists():
        raise ValueError('720p generation already attempted. Resume its saved prediction or inspect the dashboard.')
    generation = json.loads((folder / 'generation.json').read_text())
    videos = [folder / name for name in generation['local_videos']]
    images = [folder / name for name in generation['local_images']]
    validate_duration(videos)
    upload_videos = [upload_video(p, folder, index) for index,p in enumerate(videos,1)]
    payload = {'input': dict(json.loads((folder / 'seedance-request.json').read_text())['input'])}
    payload['input'].update(resolution='720p', reference_videos=[upload_file(p) for p in upload_videos],
                            reference_images=[upload_file(p) for p in images])
    shutil.copy2(folder / 'upload.mp4', hd / 'upload.mp4')
    return queue(hd, payload, 'response.json')


def saved_provider(folder):
    folder = Path(folder)
    for name in ['generation.json', 'seedance-response.json', 'response.json']:
        path = folder / name
        if path.exists():
            return json.loads(path.read_text()).get('provider', 'legacy')
    return 'legacy'
