"""Project-local runtime paths for Windows and POSIX."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def face_python():
    return ROOT / ('.venv-face/Scripts/python.exe' if os.name == 'nt' else '.venv-face/bin/python')


def add_local_tools():
    for directory in [ROOT/'tools/rubberband', ROOT/'tools/rubberband/rubberband-4.0.0-gpl-executable-windows']:
        if (directory/'rubberband.exe').exists() and str(directory) not in os.environ.get('PATH','').split(os.pathsep):
            os.environ['PATH'] = str(directory) + os.pathsep + os.environ.get('PATH', '')
