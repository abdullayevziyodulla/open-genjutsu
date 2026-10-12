"""Local WebM playback copies; generation continues to use the saved MP4."""
from pathlib import Path
import json
import shutil
import subprocess
import threading
import av

FILES = {'seedance-input.mp4', 'original.mp4', 'depth.mp4', 'mask.mp4'}
_locks = {}
_guard = threading.Lock()


def preview(folder, name, kind='webm'):
    if name not in FILES or kind not in {'webm', 'jpg'}:
        raise ValueError('Unknown preview.')
    folder = Path(folder)
    source = folder / name
    info = source.stat()
    stamp = {'size': info.st_size, 'mtime_ns': info.st_mtime_ns}
    target = folder / 'browser-previews' / (source.stem + '.' + kind)
    metadata = target.with_suffix('.' + kind + '.json')
    with _guard:
        lock = _locks.setdefault(str(target), threading.Lock())
    with lock:
        if target.exists() and metadata.exists() and json.loads(metadata.read_text()) == stamp:
            return target
        target.parent.mkdir(exist_ok=True)
        temporary = target.with_name(target.stem + '.pending.' + kind)
        try:
            if kind == 'jpg':
                with av.open(str(source)) as clip:
                    next(clip.decode(video=0)).to_image().save(temporary, quality=95)
            else:
                ffmpeg = shutil.which('ffmpeg')
                if not ffmpeg:
                    raise ValueError('FFmpeg is required for the browser playback copy.')
                subprocess.run([
                    ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-i', str(source),
                    '-map', '0:v:0', '-map', '0:a:0?', '-c:v', 'libvpx-vp9',
                    '-lossless', '1', '-deadline', 'realtime', '-cpu-used', '8',
                    '-row-mt', '1', '-threads', '4', '-c:a', 'libopus', '-b:a', '192k',
                    str(temporary),
                ], check=True, capture_output=True, timeout=180)
            temporary.replace(target)
            metadata.write_text(json.dumps(stamp))
        finally:
            temporary.unlink(missing_ok=True)
    return target
