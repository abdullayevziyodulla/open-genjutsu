from pathlib import Path
import threading,uuid,shutil,json
from fastapi import FastAPI,UploadFile,File,Form,HTTPException,Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pipeline import run
ROOT=Path(__file__).resolve().parent
RUNS=ROOT/'runs';RUNS.mkdir(exist_ok=True)
app=FastAPI();jobs={};generation_lock=threading.Lock()
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
app.add_middleware(TrustedHostMiddleware,allowed_hosts=['127.0.0.1','localhost','[::1]','testserver'])

@app.middleware('http')
async def local_mutations(request:Request,call_next):
    if request.method not in ['GET','HEAD','OPTIONS']:
        origin=request.headers.get('origin')
        if (origin and origin!=str(request.base_url).rstrip('/')) or request.headers.get('sec-fetch-site')=='cross-site':
            return JSONResponse({'detail':'Submit requests from the local app.'},status_code=403)
    return await call_next(request)
@app.get('/')
def index():return FileResponse(ROOT/'static/index.html')
@app.post('/jobs')
def create(video:UploadFile=File(...),prompt:str=Form('person'),provider:str=Form('replicate'),mode:str=Form('depth'),
           sirio:UploadFile|None=File(None),tein:UploadFile|None=File(None),generation_prompt:str=Form(''),engine:str=Form('seedance')):
    if mode not in ['depth','face_mesh','depth_mesh']:raise HTTPException(400,'Unknown workflow mode')
    if provider not in ['huggingface','replicate','replicate-chenxwh']:raise HTTPException(400,'Unknown provider')
    if engine not in ['seedance','wan']:raise HTTPException(400,'Unknown generation model')
    for index,reference in enumerate([sirio,tein]):
        if reference and Path(reference.filename or '').suffix.lower() not in (['.png','.jpg','.jpeg','.webp']+(['.mp4','.mov','.webm'] if index==0 and engine=='seedance' else [])):
            raise HTTPException(400,'Unsupported character reference format.')
    ident=uuid.uuid4().hex;folder=RUNS/ident;folder.mkdir();src=folder/'upload.mp4'
    with src.open('wb') as out:shutil.copyfileobj(video.file,out)
    for name,reference in [('sirio',sirio),('tein',tein)]:
        if reference:
            with (folder/(name+'-reference'+Path(reference.filename).suffix.lower())).open('wb') as out:
                shutil.copyfileobj(reference.file,out)
    (folder/'pending-creative.json').write_text(json.dumps({'prompt':generation_prompt,'engine':engine}))
    jobs[ident]={'state':'running','status':'Starting','id':ident}
    def work():
        try:
            if mode=='face_mesh':
                from face_mesh import run as run_mesh
                run_mesh(src,folder,lambda s:jobs[ident].update(status=s))
            elif mode=='depth_mesh':
                from face_mesh import run_depth
                run_depth(src,folder,prompt,provider,lambda s:jobs[ident].update(status=s))
            else:run(src,folder,prompt,provider,lambda s:jobs[ident].update(status=s))
            jobs[ident].update(state='done',status='Preparation complete · input review required')
            (folder/'status.json').write_text(json.dumps(jobs[ident]))
        except Exception as e:
            jobs[ident].update(state='error',status=str(e))
            (folder/'status.json').write_text(json.dumps(jobs[ident]))
    threading.Thread(target=work,daemon=True).start();return jobs[ident]
@app.get('/jobs/{ident}')
def get(ident:str):
    if ident not in jobs:
        if len(ident)==32 and all(c in '0123456789abcdef' for c in ident) and (RUNS/ident/'status.json').exists():return json.loads((RUNS/ident/'status.json').read_text())
        raise HTTPException(404)
    return jobs[ident]
@app.post('/jobs/{ident}/seedance')
def seedance(ident:str,prompt:str=Form(...),sirio:UploadFile=File(...),tein:UploadFile|None=File(None),engine:str=Form('seedance'),reviewed_plan:str=Form('')):
    if len(ident)!=32 or not all(c in '0123456789abcdef' for c in ident):raise HTTPException(404)
    folder=RUNS/ident
    from config import setting
    provider=setting('GENERATION_PROVIDER','oxen')
    if provider=='oxen':
        if engine!='seedance':raise HTTPException(400,'Oxen is selected for Seedance 2.5 draft generation.')
        if not setting('OXEN_API_KEY').strip():raise HTTPException(400,'Add your Oxen API key in the connection form first. No uploads or generation submitted.')
    if provider=='lec':
        if engine!='seedance':raise HTTPException(400,'Lec is selected for raw Seedance 2.5 generation.')
        if not setting('LEC_API_KEY').strip():raise HTTPException(400,'Add your Lec API key in the connection form first. No uploads or generation submitted.')
    if engine not in ['seedance','wan']:raise HTTPException(400,'Unknown generation model.')
    if engine=='wan' and tein:raise HTTPException(400,'Wan supports one character reference image.')
    if not (folder/'audio-manifest.json').exists():raise HTTPException(400,'Audio separation must complete first.')
    from mask_review import require_approved
    try:require_approved(folder)
    except ValueError as e:raise HTTPException(409,str(e))
    with generation_lock:
        if jobs.get(ident,{}).get('state')=='running' or (folder/'submission-intent.json').exists() or (folder/'seedance-response.json').exists():
            raise HTTPException(409,'This job is already running or was submitted. Inspect its saved request.')
        paths=[]
        for name,upload in [('sirio-reference',sirio),('tein-reference',tein)]:
            if upload is None:
                paths.append(None)
                continue
            suffix=Path(upload.filename or '').suffix.lower()
            allowed=['.png','.jpg','.jpeg','.webp']
            if name=='sirio-reference' and engine=='seedance':allowed+=['.mp4','.mov','.webm']
            if suffix not in allowed:raise HTTPException(400,'Use a character image; Seedance also supports an identity video.')
            path=folder/(name+suffix)
            with path.open('wb') as f:shutil.copyfileobj(upload.file,f)
            paths.append(path)
        if provider=='lec':
            from lec_seedance import plan,plan_hash
            try:
                payload,videos,images=plan(folder,prompt,*paths)
                expected=plan_hash(payload,videos,images)
            except ValueError as e:raise HTTPException(400,str(e))
            if reviewed_plan!=expected:raise HTTPException(409,'Review the current Lec prompt and references first.')
            (folder/'lec-plan-review.json').write_text(json.dumps({'hash':expected}))
        if provider=='oxen':
            from oxen_seedance import plan,plan_hash
            try:
                payload,videos,images=plan(folder,prompt,*paths)
                expected=plan_hash(payload,videos,images)
            except (ValueError,OSError) as e:raise HTTPException(400,str(e))
            if reviewed_plan!=expected:raise HTTPException(409,'Review the current Oxen prompt and references first.')
            (folder/'oxen-plan-review.json').write_text(json.dumps({'hash':expected}))
        label={'lec':'Lec','oxen':'Oxen'}.get(provider,'Replicate')
        jobs[ident]={'id':ident,'state':'running','stage':'submission','status':'Uploading references to '+label+' · '+('Wan 2.2' if engine=='wan' else 'Seedance 2.5')}
        (folder/'preferred-engine.json').write_text(json.dumps({'engine':engine}))
        def save():(folder/'status.json').write_text(json.dumps(jobs[ident]))
        save()
    def collect():
        from seedance_bridge import wait_and_finish
        if engine=='wan':
            from wan_bridge import submit
        else:
            from seedance_bridge import submit
        def update(message):jobs[ident].update(status=message);save()
        try:
            request_id=submit(folder,prompt,*paths,status=update)
            jobs[ident].update(stage='generation',request_id=request_id);save()
            wait_and_finish(folder,request_id,update)
            jobs[ident].update(state='done',status='Final preview ready · entire original source audio',final_url='/runs/'+ident+'/final-preview.mp4')
        except Exception as e:jobs[ident].update(state='error',status=str(e))
        save()
    threading.Thread(target=collect,daemon=True).start()
    return {'id':ident,'state':'running','status':jobs[ident]['status']}

@app.post('/jobs/{ident}/lec-plan')
def lec_plan(ident:str,prompt:str=Form(...),sirio:UploadFile=File(...),tein:UploadFile|None=File(None)):
    """Offline request preview; nothing is uploaded to a provider or billed."""
    import tempfile
    from lec_seedance import plan,plan_hash
    folder=hd_folder(ident)
    with tempfile.TemporaryDirectory() as scratch:
        refs=[]
        for index,upload in enumerate([sirio,tein]):
            if upload is None:
                refs.append(None);continue
            suffix=Path(upload.filename or '').suffix.lower()
            if suffix not in ['.jpg','.jpeg','.png','.webp','.mp4','.webm']:
                raise HTTPException(400,'Use JPEG, PNG, WebP, MP4 or WebM for Lec.')
            path=Path(scratch)/(str(index)+suffix)
            with path.open('wb') as out:shutil.copyfileobj(upload.file,out)
            refs.append(path)
        try:
            payload,videos,images=plan(folder,prompt,*refs)
        except ValueError as e:raise HTTPException(400,str(e))
        preview={'prompt':payload['prompt'],'user_prompt':prompt,'duration':payload['duration'],'aspect_ratio':payload['aspect_ratio'],
                'resolution':'720p','price_cny':4.5,'upload_price_usd':round(0.05*len(videos)+0.01*len(images),2),
                'hash':plan_hash(payload,videos,images)}
        (folder/'lec-request-preview.json').write_text(json.dumps(preview,indent=2))
        return preview

@app.post('/jobs/{ident}/oxen-plan')
def oxen_plan(ident:str,prompt:str=Form(...),sirio:UploadFile=File(...),tein:UploadFile|None=File(None)):
    """Build a reviewed draft request locally, without uploading or charging."""
    import tempfile
    from oxen_seedance import preview
    folder=hd_folder(ident)
    with tempfile.TemporaryDirectory() as scratch:
        refs=[]
        for index,upload in enumerate([sirio,tein]):
            if upload is None:
                refs.append(None);continue
            suffix=Path(upload.filename or '').suffix.lower()
            if suffix not in ['.jpg','.jpeg','.png','.webp','.mp4','.mov','.webm']:
                raise HTTPException(400,'Use an image or video identity reference.')
            path=Path(scratch)/(str(index)+suffix)
            with path.open('wb') as out:shutil.copyfileobj(upload.file,out)
            refs.append(path)
        try:
            result=preview(folder,prompt,*refs)
        except (ValueError,OSError) as e:raise HTTPException(400,str(e))
        (folder/'oxen-request-preview.json').write_text(json.dumps(result,indent=2))
        return result

@app.post('/jobs/{ident}/finish')
def finish(ident:str,video:UploadFile=File(...)):
    if len(ident)!=32 or not all(c in '0123456789abcdef' for c in ident):raise HTTPException(404)
    folder=RUNS/ident
    if not (folder/'upload.mp4').exists():raise HTTPException(400,'Original source is required.')
    target=folder/'seedance-result.mp4'
    with target.open('wb') as f:shutil.copyfileobj(video.file,f)
    from audio_workflow import finish_preview
    try:finish_preview(target,folder)
    except Exception as e:raise HTTPException(400,str(e))
    return {'url':'/runs/'+ident+'/final-preview.mp4'}

app.mount('/runs' ,StaticFiles(directory=RUNS),name='runs')

hd_jobs={}
hd_lock=threading.Lock()
retry_lock=threading.Lock()

def hd_folder(ident):
    if len(ident)!=32 or not all(c in '0123456789abcdef' for c in ident):raise HTTPException(404)
    folder=RUNS/ident
    if not folder.exists():raise HTTPException(404)
    return folder

@app.get('/jobs/{ident}/browser-preview/{name}/{kind}')
def browser_preview(ident:str,name:str,kind:str):
    from browser_preview import preview
    folder=hd_folder(ident)
    try:target=preview(folder,name,kind)
    except FileNotFoundError:raise HTTPException(404,'Prepared video not found.')
    except ValueError as e:raise HTTPException(400,str(e))
    return FileResponse(target,media_type='video/webm' if kind=='webm' else 'image/jpeg',headers={'Cache-Control':'no-cache'})

@app.post('/jobs/{ident}/retry-preview')
def retry_preview(ident:str):
    from preview_retry import prepare_retry,submit_retry
    folder=hd_folder(ident)
    with retry_lock:
        try:target,created=prepare_retry(folder)
        except ValueError as e:raise HTTPException(409,str(e))
        retry_id=target.name
        if not created:return {'id':retry_id,'url':'/?job='+retry_id+'#generation-progress'}
        jobs[retry_id]={'id':retry_id,'state':'running','stage':'submission',
                        'status':'Uploading corrected references to Replicate…'}
        def save(): (target/'status.json').write_text(json.dumps(jobs[retry_id]))
        save()
        def work_retry():
            from replicate_seedance import wait_and_finish
            def update(message):
                jobs[retry_id].update(status=message);save()
            try:
                request_id=submit_retry(target,update)
                jobs[retry_id].update(stage='generation',request_id=request_id);save()
                wait_and_finish(target,request_id,update)
                jobs[retry_id].update(state='done',status='Final preview ready · original source audio restored',
                                     final_url='/runs/'+retry_id+'/final-preview.mp4')
            except Exception as e:jobs[retry_id].update(state='error',status=str(e))
            save()
        threading.Thread(target=work_retry,daemon=True).start()
        return {'id':retry_id,'url':'/?job='+retry_id+'#generation-progress'}

@app.post('/jobs/{ident}/resume-upload')
def resume_upload(ident:str):
    """User-triggered recovery only where no generation request was sent."""
    from oxen_seedance import recover_upload,submit,wait_and_finish
    folder=hd_folder(ident)
    with generation_lock:
        if jobs.get(ident,{}).get('state')=='running':raise HTTPException(409,'This job is already running.')
        try:prompt,references=recover_upload(folder)
        except (ValueError,OSError,KeyError) as exc:raise HTTPException(409,str(exc))
        jobs[ident]={'id':ident,'state':'running','stage':'submission','status':'Verifying private Oxen media for the reviewed 480p draft'}
        def save():(folder/'status.json').write_text(json.dumps(jobs[ident]))
        save()
    def work():
        def update(message):jobs[ident].update(status=message);save()
        try:
            request_id=submit(folder,prompt,*references,status=update)
            jobs[ident].update(stage='generation',request_id=request_id);save()
            wait_and_finish(folder,request_id,update)
            jobs[ident].update(state='done',status='Final preview ready · entire original source audio',final_url='/runs/'+ident+'/final-preview.mp4')
        except Exception as exc:jobs[ident].update(state='error',status=str(exc))
        save()
    threading.Thread(target=work,daemon=True).start()
    return {'id':ident,'state':'running'}

@app.post('/jobs/{ident}/revise-preview')
def revise_preview(ident:str):
    from preview_retry import prepare_retry
    folder=hd_folder(ident)
    with retry_lock:
        try:target,created=prepare_retry(folder,revise=True)
        except ValueError as e:raise HTTPException(409,str(e))
        if created:
            jobs[target.name]={'id':target.name,'state':'done',
                'status':'Prepared input retained. Change the character reference or prompt before creating a new billed preview.'}
            (target/'status.json').write_text(json.dumps(jobs[target.name]))
        return {'id':target.name,'url':'/?job='+target.name+'#draft'}

@app.get('/jobs/{ident}/hd')
def get_hd(ident:str):
    folder=hd_folder(ident)
    if ident in hd_jobs:return hd_jobs[ident]
    saved=folder/'hd/status.json'
    if saved.exists():return json.loads(saved.read_text())
    from config import setting
    return {'state':'idle','status':'Approve your preview to generate 720p (a new billed generation).' if setting('GENERATION_PROVIDER')=='replicate' else 'Approve your draft to generate 1080p.'}

@app.post('/jobs/{ident}/hd')
def create_hd(ident:str):
    folder=hd_folder(ident)
    from replicate_seedance import saved_provider
    if saved_provider(folder)=='lec':raise HTTPException(400,'Lec already generates 720p; no HD upgrade is available.')
    with hd_lock:
        previous=get_hd(ident)
        if previous['state'] in ['running','done']:return previous
        if not (folder/'final-preview.mp4').exists():raise HTTPException(400,'Complete and review a draft first.')
        hd=folder/'hd';hd.mkdir(exist_ok=True)
        from replicate_seedance import saved_provider
        message='Submitting a new approved 720p generation' if saved_provider(folder)=='replicate' else 'Submitting approved draft for 1080p'
        hd_jobs[ident]={'state':'running','status':message,'id':ident}
        def save(): (hd/'status.json').write_text(json.dumps(hd_jobs[ident]))
        save()
    def work_hd():
        from seedance_bridge import submit_hd,wait_and_finish
        try:
            request_id=submit_hd(folder)
            from replicate_seedance import saved_provider
            quality='720p' if saved_provider(hd)=='replicate' else '1080p'
            hd_jobs[ident].update(request_id=request_id,status='Generating '+quality);save()
            wait_and_finish(hd,request_id,lambda s:hd_jobs[ident].update(status=s))
            hd_jobs[ident].update(state='done',status=quality+' ready · original source audio restored')
        except Exception as e:hd_jobs[ident].update(state='error',status=str(e))
        save()
    threading.Thread(target=work_hd,daemon=True).start()
    return hd_jobs[ident]

@app.get('/jobs/{ident}/mask-review')
def get_mask_review(ident:str):
    from mask_review import state
    return state(hd_folder(ident))

@app.get('/jobs/{ident}/generation-status')
def get_generation_status(ident:str,hd:bool=False):
    from generation_status import snapshot
    folder=hd_folder(ident)
    return snapshot(folder/'hd' if hd else folder, (hd_jobs if hd else jobs).get(ident))

@app.post('/jobs/{ident}/mask-review')
def save_mask_review(ident:str,approved:bool=Form(...),fingerprint:str=Form(...),note:str=Form('')):
    from mask_review import review
    try:return review(hd_folder(ident),approved,note,fingerprint)
    except ValueError as e:raise HTTPException(409,str(e))

app.mount('/static',StaticFiles(directory=ROOT/'static'),name='static')

@app.on_event('startup')
def resume_saved_generations():
    """Resume collection only: never requeue a paid prediction on restart."""
    from seedance_bridge import wait_and_finish
    for root in RUNS.iterdir():
        if not root.is_dir() or len(root.name)!=32:continue
        for folder,response_file,registry in [(root,'seedance-response.json',jobs),(root/'hd','response.json',hd_jobs)]:
            response=folder/response_file
            if not response.exists() or (folder/'final-preview.mp4').exists():continue
            from generation_status import read_json
            if (read_json(folder/'provider-status.json') or read_json(response)).get('status') in ['failed','canceled','cancelled','FAILED','CANCELED']:continue
            try:request_id=json.loads(response.read_text()).get('requestId')
            except (ValueError,OSError):continue
            if not request_id:continue
            registry[root.name]={'id':root.name,'state':'running','status':'Resuming saved request '+request_id}
            def collect_saved(folder=folder,ident=root.name,request_id=request_id,registry=registry):
                try:
                    wait_and_finish(folder,request_id,lambda message:registry[ident].update(status=message))
                    registry[ident].update(state='done',status='Final preview ready · original source audio')
                except Exception as e:registry[ident].update(state='error',status=str(e))
                (folder/'status.json').write_text(json.dumps(registry[ident]))
            threading.Thread(target=collect_saved,daemon=True).start()

@app.get('/health')
def health():
    return {'status':'ok','service':'Open Genjutsu Video Workflow'}

@app.get('/configuration')
def configuration():
    from config import setting
    provider=setting('GENERATION_PROVIDER','oxen')
    return {'provider':provider,'replicate_token_configured':bool(setting('REPLICATE_API_TOKEN').strip()),
            'oxen_key_configured':bool(setting('OXEN_API_KEY').strip()),
            'lec_key_configured':bool(setting('LEC_API_KEY').strip()),
            'oxen_storage_repo':setting('OXEN_STORAGE_REPO'),
            'preview_resolution':'720p' if provider=='lec' else '480p' if provider in ['replicate','oxen'] else 'draft',
            'final_resolution':'720p' if provider in ['lec','replicate'] else '1080p',
            'supports_hd':provider!='lec', 'generation_price_cny':4.5 if provider=='lec' else None}

@app.post('/configuration/lec')
def configure_lec(request:Request,api_key:str=Form(...)):
    from config import save_setting
    # Do not accept credential writes from an unrelated website.
    origin=request.headers.get('origin')
    if origin and origin!=str(request.base_url).rstrip('/'):
        raise HTTPException(403,'Open this form in the local workflow app.')
    if request.client and request.client.host not in ['127.0.0.1','::1','testclient']:
        raise HTTPException(403,'Local connection required.')
    if not api_key.strip() or any(char in api_key for char in '\r\n'):
        raise HTTPException(400,'Enter a single-line Lec API key.')
    with generation_lock:
        save_setting('LEC_API_KEY',api_key.strip())
        save_setting('GENERATION_PROVIDER','lec')
    return {'configured':True,'provider':'lec'}

@app.post('/configuration/oxen')
def configure_oxen(request:Request,api_key:str=Form(...)):
    from config import save_setting
    origin=request.headers.get('origin')
    if origin and origin!=str(request.base_url).rstrip('/'):
        raise HTTPException(403,'Open this form in the local workflow app.')
    if request.client and request.client.host not in ['127.0.0.1','::1','testclient']:
        raise HTTPException(403,'Local connection required.')
    if not api_key.strip() or any(char in api_key for char in '\r\n'):
        raise HTTPException(400,'Enter a single-line Oxen API key.')
    with generation_lock:
        save_setting('OXEN_API_KEY',api_key.strip())
        save_setting('GENERATION_PROVIDER','oxen')
    return {'configured':True,'provider':'oxen'}

@app.get('/library')
def library():
    """Local history: no credentials, provider responses or signed URLs."""
    items=[]
    for folder in RUNS.iterdir():
        if not folder.is_dir() or len(folder.name)!=32 or any(c not in '0123456789abcdef' for c in folder.name):continue
        try:
            state=json.loads((folder/'status.json').read_text())
        except (OSError,ValueError):continue
        items.append({'id':folder.name,'state':jobs.get(folder.name,state).get('state','done'),
                      'has_result':(folder/'final-preview.mp4').exists(),
                      'modified':(folder/'status.json').stat().st_mtime})
    return {'jobs':sorted(items,key=lambda item:item['modified'],reverse=True)[:30]}

@app.get('/guide')
def guide():return FileResponse(ROOT/'static/guide.html')

@app.post('/configuration/settings')
def configure_settings(request:Request,provider:str=Form(...),replicate_token:str=Form(''),storage_repo:str=Form('')):
    from config import save_setting
    import re
    origin=request.headers.get('origin')
    if origin and origin!=str(request.base_url).rstrip('/'):
        raise HTTPException(403,'Open settings in the local app.')
    if request.client and request.client.host not in ['127.0.0.1','::1','testclient']:
        raise HTTPException(403,'Local connection required.')
    if provider not in ['oxen','replicate','lec']:
        raise HTTPException(400,'Choose a supported generation provider.')
    if any(c in replicate_token for c in '\r\n'):
        raise HTTPException(400,'Use a single-line token.')
    storage_repo=storage_repo.strip()
    if storage_repo and not re.fullmatch(r'[\w-]+/[\w.-]+',storage_repo):
        raise HTTPException(400,'Use namespace/repository for private Oxen storage.')
    with generation_lock:
        if any(job.get('state')=='running' for job in [*jobs.values(),*hd_jobs.values()]):
            raise HTTPException(409,'Wait for active processing to finish before changing API settings.')
        if replicate_token.strip():save_setting('REPLICATE_API_TOKEN',replicate_token.strip())
        save_setting('OXEN_STORAGE_REPO',storage_repo)
        save_setting('GENERATION_PROVIDER',provider)
    return {'configured':True,'provider':provider}
