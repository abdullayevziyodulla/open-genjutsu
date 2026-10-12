"""Offline checks; never prints credential values or starts paid calls."""
import argparse,importlib,shutil,sys
from config import setting

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--require-keys',action='store_true');parser.add_argument('--mesh',action='store_true');args=parser.parse_args()
    failed=sys.version_info<(3,12)
    print('Python:',sys.version.split()[0], '(3.12+ required)')
    for name in ['av','numpy','PIL','requests','fastapi','uvicorn','multipart','gradio_client','scipy','cv2']:
        try:importlib.import_module(name);print(name+': OK')
        except Exception as exc:print(name+': FAILED ('+type(exc).__name__+')');failed=True
    binary=shutil.which('rubberband');print('rubberband:', 'OK' if binary else 'MISSING — see docs/SETUP-AGENT.md');failed=failed or not binary
    if args.mesh:
        from pathlib import Path
        import subprocess
        from runtime_paths import face_python
        worker=face_python()
        ready=worker.exists() and subprocess.run([str(worker),'-c','import mediapipe,av,PIL,numpy'],capture_output=True).returncode==0
        print('Face mesh worker: '+('OK' if ready else 'MISSING — run bash setup-face-mesh.sh'))
        failed=failed or not ready
    missing=[]
    provider=setting('GENERATION_PROVIDER','oxen')
    if provider not in ['replicate','lec','oxen']:
        print('GENERATION_PROVIDER must be replicate, lec or oxen');failed=True
    print('Generation provider:',provider)
    for key in (['OXEN_API_KEY','REPLICATE_API_TOKEN'] if provider=='oxen' else ['LEC_API_KEY','REPLICATE_API_TOKEN'] if provider=='lec' else ['REPLICATE_API_TOKEN'] if provider=='replicate' else ['REPLICATE_API_TOKEN']):
        value=setting(key).strip()
        valid=bool(value) and not any(x in value.lower() for x in ['your_key','your_api','replace_me','placeholder'])
        print(key+': '+('configured (not verified remotely)' if valid else 'MISSING'))
        if not valid:missing.append(key)
    if failed:print('DEPENDENCIES NOT READY');return 1
    if missing:
        if provider=='oxen':
            print('LOCAL UI READY; add the missing preparation/generation keys above.')
            return 2 if args.require_keys else 0
        if provider=='lec':
            print('LOCAL UI READY; Lec generation needs LEC_API_KEY. Replicate remains the preparation provider.')
            return 2 if args.require_keys else 0
        print('LOCAL UI READY; GENERATION BLOCKED until your Replicate token is configured.' if provider=='replicate' else 'LOCAL UI READY; add the missing provider keys.')
        return 2 if args.require_keys else 0
    print('LOCAL SETUP READY; provider access/balance has not been verified by this offline check.')
    return 0
if __name__=='__main__':sys.exit(main())
