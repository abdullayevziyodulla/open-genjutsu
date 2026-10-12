"""Replicate photo-based character replacement with original soundtrack delivery."""
import json
import shutil
from pathlib import Path

import av
from PIL import Image
from mask_review import require_approved
from replicate_seedance import upload_file,queue

MODEL='wan-video/wan-2.2-animate-replace'
BRIEF=('Replace the main character in the original video with the character in the supplied photo. '
       'Use the original video for movement, facial expressions, background and timing. '
       'Restore the entire original source soundtrack in the delivered preview. '
       'Wan uses video and photo inputs; it does not accept a text prompt.')


def media(folder, reference):
    folder,reference=Path(folder),Path(reference)
    if reference.suffix.lower() not in ['.png','.jpg','.jpeg','.webp']:
        raise ValueError('Wan character replacement requires one character image.')
    with Image.open(reference) as image:image.verify()
    source=folder/'upload.mp4'
    if not source.is_file():raise ValueError('Original source video is missing.')
    with av.open(str(source)) as video:
        if not video.streams.video or not video.streams.audio:
            raise ValueError('The original video must contain video and its source soundtrack.')
        duration=video.duration/av.time_base
    if not 0<duration<=30.05:raise ValueError('Use a source clip of up to 30 seconds for this workflow.')
    return source


def submit(folder,prompt,reference,second=None,status=print):
    folder=Path(folder);require_approved(folder)
    if (folder/'seedance-response.json').exists() or (folder/'submission-intent.json').exists():
        raise ValueError('This job has already been attempted. Inspect or resume its saved prediction.')
    if second:raise ValueError('Wan replacement uses one character image; remove the optional second reference.')
    reference=Path(reference).resolve()
    source=media(folder,reference)
    local=folder/('replicate-reference-1'+reference.suffix.lower())
    if local.resolve()!=reference:shutil.copy2(reference,local)
    status('Uploading original video and character photo to Replicate · Wan 2.2')
    payload={'input':{'video':upload_file(source),'character_image':upload_file(local),
                      'resolution':'480','go_fast':True,'merge_audio':False}}
    ident=queue(folder,payload,'seedance-response.json',model=MODEL)
    (folder/'generation.json').write_text(json.dumps({'provider':'replicate','model':MODEL,
        'request_id':ident,'mode':'character_replacement','resolution':'480p',
        'prompt':BRIEF,'user_prompt':prompt,'video':'seedance-result.mp4',
        'local_videos':['upload.mp4'],'local_images':[local.name]},indent=2))
    status('Wan 2.2 accepted your 480p character replacement request: '+ident)
    return ident


def submit_hd(folder):
    folder=Path(folder);require_approved(folder)
    if not (folder/'final-preview.mp4').exists():raise ValueError('Complete and review the 480p preview first.')
    hd=folder/'hd';hd.mkdir(exist_ok=True)
    if (hd/'response.json').exists() or (hd/'submission-intent.json').exists():
        raise ValueError('720p generation already attempted. Resume the saved prediction.')
    generation=json.loads((folder/'generation.json').read_text())
    reference=folder/generation['local_images'][0]
    source=media(folder,reference)
    payload={'input':dict(json.loads((folder/'seedance-request.json').read_text())['input'])}
    payload['input'].update(resolution='720',video=upload_file(source),character_image=upload_file(reference))
    shutil.copy2(source,hd/'upload.mp4')
    return queue(hd,payload,'response.json',model=MODEL)
