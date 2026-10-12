#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
FACE_PYTHON="${FACE_PYTHON:-python3.12}"
"$FACE_PYTHON" -m venv .venv-face
.venv-face/bin/python -m pip install mediapipe==1.1.0 av==19.0.1 pillow==12.3.0 numpy==2.5.3
