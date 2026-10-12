"""Run the local studio. No tunnels, uploads or model calls on launch."""
import os
import json
from pathlib import Path
import uvicorn
if __name__=='__main__':
    port=int(os.getenv('PORT','8770'))
    state=Path(__file__).resolve().parent/'.runtime-server.json'
    state.write_text(json.dumps({'pid':os.getpid(),'port':port},indent=2))
    try:
        uvicorn.run('app:app',host='127.0.0.1',port=port)
    finally:
        try:
            if json.loads(state.read_text()).get('pid')==os.getpid():state.unlink()
        except (OSError,ValueError):pass
