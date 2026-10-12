"""Export allowlisted source only; never copy a live installation wholesale."""
import argparse
import hashlib
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
FILES={'LICENSE','NOTICE','README.md','START-HERE.md','THIRD-PARTY.md','CONTRIBUTING.md',
       'SECURITY.md','AGENTS.md','.gitignore','.env.example','requirements.txt',
       'setup.sh','setup-face-mesh.sh','start.command','Start-Open-Genjutsu.cmd','Stop-Open-Genjutsu.cmd',
       'Stop-Genjustsu.ps1'}
PYTHON={'app.py','audio_workflow.py','browser_preview.py','config.py','doctor.py','face_mesh.py',
        'generation_status.py','launch.py','lec_seedance.py','mask_review.py','media_host.py',
        'mesh_worker.py','oxen_media.py','oxen_seedance.py','pipeline.py','preview_retry.py',
        'raw_masks.py','replicate_seedance.py','runtime_paths.py','seedance_bridge.py',
        'seedance_media.py','start-windows.py','test_composite.py','wan_bridge.py','workflow.py'}

def source_files(root=ROOT):
    selected=[root/name for name in sorted(FILES|PYTHON) if (root/name).is_file()]
    for directory,suffixes in [('static',{'.html','.css','.js'}),('docs',{'.md','.jpg'}),
                               ('tests',{'.py'}),('scripts',{'.py'}),('.github',{'.yml','.md'}),
                               ('.agents',{'.md'})]:
        selected.extend(p for p in (root/directory).rglob('*') if p.is_file() and p.suffix in suffixes
                        and '__pycache__' not in p.parts)
    for path in selected:
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError('Release source cannot include external links: '+str(path))
    return sorted(selected)

def package(output,root=ROOT):
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    entries=source_files(root)
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for path in entries:
            archive.write(path,'Open-Genjutsu/'+path.relative_to(root).as_posix())
    digest=hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix('.zip.sha256').write_text(digest+'  '+output.name+'\n')
    return len(entries)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'dist/Open-Genjutsu-source.zip')
    args=parser.parse_args();count=package(args.output)
    print(f'Exported {count} source files to {args.output}')
