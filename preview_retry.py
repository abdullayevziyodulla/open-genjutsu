"""Reuse approved preparation for one explicit retry, retaining the failed attempt."""
import json
import shutil
import uuid
from pathlib import Path

from generation_status import read_json
from mask_review import require_approved
from replicate_seedance import saved_provider

EXCLUDE = {'seedance-request.json', 'seedance-response.json', 'generation.json',
           'provider-status.json', 'status.json', 'submission-intent.json',
           'submission-error.json', 'seedance-result.mp4', 'final-preview.mp4',
           'hd', 'retry-preview.json', 'retry-source.json'}


def prepare_retry(source, revise=False):
    """Caller holds the retry lock; a persisted link prevents repeated submissions."""
    source = Path(source)
    link_name='revision-preview.json' if revise else 'retry-preview.json'
    linked = read_json(source/link_name).get('id')
    if linked:
        if len(linked)!=32 or any(c not in '0123456789abcdef' for c in linked):
            raise ValueError('Invalid saved retry ID.')
        if not (source.parent/linked).is_dir():
            raise ValueError('The saved retry folder is missing. Inspect it before another submission.')
        return source.parent/linked, False
    provider = read_json(source/'provider-status.json') or read_json(source/'seedance-response.json')
    if saved_provider(source)!='replicate' or provider.get('status') not in ['failed', 'canceled']:
        raise ValueError('Retry is available only after Replicate confirms a failed or canceled prediction.')
    if 'E005' in str(provider.get('error','')) and not revise:
        raise ValueError('Replicate flagged this input as sensitive (E005). Change the reference or prompt before submitting a new request.')
    require_approved(source)
    generation = read_json(source/'generation.json')
    if not generation.get('prompt') or not generation.get('local_videos'):
        raise ValueError('Saved prompt and references are required for a retry.')
    for name in generation['local_videos'] + generation.get('local_images', []):
        if Path(name).name!=name or not (source/name).is_file():
            raise ValueError('A saved reference is missing or invalid.')
    target = source.parent/uuid.uuid4().hex
    shutil.copytree(source, target, ignore=lambda path,names: (EXCLUDE|{'revision-preview.json','revision-source.json'}).intersection(names))
    require_approved(target)
    (target/('revision-source.json' if revise else 'retry-source.json')).write_text(json.dumps({
        'id':source.name, 'generation':generation, 'provider_error':provider.get('error')},indent=2))
    # Persist before the worker starts: opening the old job again follows this attempt.
    (source/link_name).write_text(json.dumps({'id':target.name},indent=2))
    return target, True


def submit_retry(folder, status=print):
    from replicate_seedance import submit
    folder = Path(folder)
    generation = read_json(folder/'retry-source.json')['generation']
    if generation.get('model')=='wan-video/wan-2.2-animate-replace':
        from wan_bridge import submit as wan_submit
        return wan_submit(folder,generation.get('user_prompt',''),folder/generation['local_images'][0],status=status)
    videos = generation['local_videos']
    images = generation.get('local_images', [])
    references = videos[1:] + images
    return submit(folder, generation['prompt'], folder/references[0],
                  folder/references[1] if len(references)>1 else None,
                  status=status, prompt_is_final=True)
