"""Start a project-local, detached server and open its UI."""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE = ROOT / '.runtime-server.json'


def healthy(port):
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/health', timeout=1) as response:
            return json.load(response).get('service') == 'Open Genjutsu Video Workflow'
    except Exception:
        return False


if STATE.exists():
    previous = json.loads(STATE.read_text())
    if healthy(previous['port']):
        url = f"http://127.0.0.1:{previous['port']}"
        print('Already running: ' + url)
        if '--no-browser' not in sys.argv:webbrowser.open(url)
        raise SystemExit(0)

port = None
for candidate in range(8770, 8800):
    with socket.socket() as probe:
        try:
            probe.bind(('127.0.0.1', candidate))
            port = candidate
            break
        except OSError:
            continue
if port is None:
    raise SystemExit('No free port between 8770 and 8799.')

environment = dict(os.environ, PORT=str(port), PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
with (ROOT / 'server.log').open('a', encoding='utf-8') as log:
    process = subprocess.Popen([sys.executable, str(ROOT / 'launch.py')], cwd=ROOT, env=environment,
                               stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                               creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW)
# launch.py records the actual serving PID (the venv launcher can spawn a child).
for _ in range(50):
    if healthy(port):
        url = f'http://127.0.0.1:{port}'
        print('UI running: ' + url)
        if '--no-browser' not in sys.argv:
            webbrowser.open(url)
        raise SystemExit(0)
    if process.poll() is not None:
        break
    time.sleep(.4)
raise SystemExit('The server did not become ready. See server.log.')
