"""Safe, offline view of persisted provider progress for the UI."""
import json
from datetime import datetime, timezone
from pathlib import Path


def read_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


def snapshot(folder, local=None):
    folder = Path(folder)
    submitting = bool(local and local.get('state')=='running' and local.get('stage')=='submission')
    local = local or read_json(folder/'status.json')
    response = read_json(folder/'seedance-response.json') or read_json(folder/'response.json')
    generation = read_json(folder/'generation.json')
    intent = read_json(folder/'submission-intent.json')
    revision = read_json(folder/'revision-source.json')
    preference = read_json(folder/'preferred-engine.json')
    wan = (generation.get('model') or response.get('model'))=='wan-video/wan-2.2-animate-replace' or (not generation and not response and preference.get('engine')=='wan')
    attempted = bool(response or generation or intent or submitting)
    provider = read_json(folder/'provider-status.json') or response
    provider_name = generation.get('provider') or response.get('provider') or intent.get('provider') or read_json(folder/'provider-source.json').get('provider')
    label = 'Oxen' if provider_name=='oxen' else 'Lec' if provider_name=='lec' else 'Replicate'
    ident = response.get('id') or response.get('requestId') or generation.get('request_id')
    phase = 'idle'
    message = 'Review your prepared input and references, then create a 480p preview.'
    error = None
    active = False
    if revision and not attempted:
        message='Prepared clip retained. Change the reference or prompt before creating a new preview.'
        if 'E005' in str(revision.get('provider_error','')):
            message='Previous attempt blocked by Replicate (E005). Change the reference or prompt; your prepared clip is retained.'
            error=revision['provider_error']
    if wan and not attempted:
        message='Wan 2.2 is ready to replace the character using your original video and saved photo.'
        error=None
    if attempted:
        state = provider.get('status')
        if intent.get('state')=='not_submitted' and not ident and not response:
            phase='not_submitted'
            error=str(intent.get('reason') or local.get('status') or 'Media upload failed.')
            message='Upload failed before generation. No request was sent to '+label+'.'
        elif state in ['failed', 'FAILED', 'canceled', 'cancelled', 'CANCELED']:
            phase = 'failed' if state.lower()=='failed' else 'canceled'
            error = str(provider.get('error_message') or provider.get('error') or local.get('status') or '')
            message = ('Generation failed: Replicate rejected the input (E006).' if 'E006' in error and provider_name=='replicate' else
                       'Generation '+phase+'. No preview was produced.')
            if 'E005' in error and provider_name=='replicate':
                phase='blocked'
                message='Replicate blocked the input or output as sensitive (E005). No preview was produced.'
        elif (folder/'final-preview.mp4').exists():
            phase = 'done'
            message = 'Preview ready with the original source audio restored.'
        elif local.get('state')=='error':
            phase = 'error'
            error = str(local.get('status', 'Result collection stopped.'))
            message = 'Result collection needs attention. The saved prediction will not be resubmitted.'
        elif state in ['succeeded', 'COMPLETED', 'completed']:
            phase = 'finishing'
            message = 'Generation finished. Downloading the video and restoring original audio…'
            active = True
        elif state in ['processing', 'IN_PROGRESS', 'RUNNING', 'in_progress']:
            phase = 'generating'
            message = 'Generating video on '+label+'… This page checks for updates automatically.'
            active = True
        elif state=='unknown':
            phase='unknown'
            message='The provider reports an unknown task state. Inspect the saved task; do not submit another request blindly.'
        elif ident:
            phase = 'queued'
            message = 'Request accepted. Waiting for '+label+' to start generation…'
            active = True
        elif submitting:
            phase = 'submitting'
            message = local.get('status') or 'Uploading references and submitting the preview…'
            active = True
        else:
            phase = 'unknown'
            message = 'Submission was attempted, but its outcome is uncertain. Check the provider before retrying.'
    if provider_name=='lec' and not attempted:
        message='Lec Seedance 2.5 · review your prepared input and request to generate 720p.'
    if provider_name=='oxen' and not attempted:
        message='Oxen Seedance 2.5 · reviewed depth/SAM input ready for a 480p draft.'
    started = provider.get('enqueued_at') or provider.get('created_at')
    ended = provider.get('completed_at')
    elapsed = None
    if started:
        try:
            beginning = datetime.fromtimestamp(started,timezone.utc) if isinstance(started,(int,float)) else datetime.fromisoformat(started.replace('Z','+00:00'))
            end = (datetime.fromtimestamp(ended,timezone.utc) if isinstance(ended,(int,float)) else datetime.fromisoformat(ended.replace('Z','+00:00'))) if ended else datetime.now(timezone.utc)
            elapsed = max(0, round((end-beginning).total_seconds()))
        except (ValueError, TypeError):
            pass
    checked = folder/'provider-status.json'
    return {'phase':phase, 'message':message, 'active':active, 'attempted':attempted,
            'retry_job':read_json(folder/'retry-preview.json').get('id'),
            'revision_job':read_json(folder/'revision-preview.json').get('id'),
            'revision':bool(revision),
            'engine':'wan' if wan else 'seedance',
            'prediction_id':ident, 'provider':provider_name, 'resolution':generation.get('resolution'),
            'progress':provider.get('progress'),
            'error':error, 'elapsed_seconds':elapsed, 'created_at':started,
            'completed_at':ended, 'checked_at':datetime.fromtimestamp(checked.stat().st_mtime,timezone.utc).isoformat() if checked.exists() else None,
            'prediction_url':('https://replicate.com/p/'+ident if ident and response.get('provider')=='replicate' else None)}
