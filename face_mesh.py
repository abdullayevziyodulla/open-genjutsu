"""Optional local face-mesh preparation; no depth or segmentation calls."""
from pathlib import Path
import json,subprocess,sys,shutil
ROOT=Path(__file__).resolve().parent
from runtime_paths import face_python

def run(src,folder,status=print):
    from pipeline import normalize
    from audio_workflow import separate,prepare_seedance_video
    folder=Path(folder)
    python=face_python()
    if not python.exists():raise ValueError('Fast face mesh needs setup: bash setup-face-mesh.sh (Python 3.12).')
    folder.mkdir(parents=True,exist_ok=True)
    status('Normalizing video');normalize(src,folder/'original.mp4')
    status('Tracking face mesh locally · no depth or SAM')
    subprocess.run([str(python),str(ROOT/'mesh_worker.py'),str(folder)],check=True)
    (folder/'workflow-mode.json').write_text(json.dumps({'mode':'face_mesh'}))
    separate(src,folder,status)
    prepare_seedance_video(folder)
    status('Face mesh ready · review tracking and pitched audio')


def run_depth(src,folder,prompt='person',provider='replicate',status=print):
    from pipeline import run as run_advanced
    from audio_workflow import prepare_seedance_video
    folder=Path(folder)
    python=face_python()
    if not python.exists():raise ValueError('Install face mesh first: bash setup-face-mesh.sh')
    folder.mkdir(parents=True,exist_ok=True)
    run_advanced(src,folder,prompt,provider,status)
    shutil.copy2(folder/'composite-silent.mp4',folder/'depth-composite-silent.mp4')
    status('Adding face mesh from original video onto depth composite')
    subprocess.run([str(python),str(ROOT/'mesh_worker.py'),str(folder),'--depth'],check=True)
    (folder/'workflow-mode.json').write_text(json.dumps({'mode':'depth_mesh'}))
    prepare_seedance_video(folder)
    status('Depth + face mesh ready · full mask and facial tracking review required')
