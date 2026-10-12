# Setup runbook

Read README.md. Detect the OS, install Python 3.12+ and Rubber Band through the supported package manager, create .venv and install requirements.txt. Never overwrite a populated .env. Copy .env.example only when .env does not exist. Ask the user to enter their own keys privately or use the local API settings UI. Do not submit inference during setup.

On Windows use .venv/Scripts/python.exe and Start-Open-Genjutsu.cmd. On macOS/Linux use .venv/bin/python and launch.py. The server binds to 127.0.0.1; no callback tunnel is required. Verify /health, the UI, offline tests and doctor.py. A running UI does not establish funded model access.

For experimental mesh modes, use a Python 3.12 worker and bash setup-face-mesh.sh. The default depth mode does not need this optional environment. Never download or ship model weights in the source release.
