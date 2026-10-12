"""Validate reference media and resize upload copies to Seedance's pixel limits."""
import json
import math
from pathlib import Path

import av

# BytePlus Seedance 2.5 documents 407,696 pixels; 409,600 also meets the LAS limit.
MIN_PIXELS = 409600
MAX_PIXELS = 8295044


def upload_video(source, folder, index=1):
    source,folder=Path(source),Path(folder)
    with av.open(str(source)) as inp:
        video=inp.streams.video[0]
        width,height=video.width,video.height
        rate=video.average_rate
        duration=float(video.duration*video.time_base) if video.duration else inp.duration/av.time_base
        if not 0.4<=width/height<=2.5:
            raise ValueError('Seedance reference video aspect ratio must be between 0.4 and 2.5.')
        if not rate or not 24<=float(rate)<=60:
            raise ValueError('Seedance reference video frame rate must be between 24 and 60 FPS.')
        if not (4 if index==1 else 2)<=duration<=30.05:
            raise ValueError('Seedance editing input must be 4–30 seconds; other video references must be 2–30 seconds.')
        if source.stat().st_size>200*1024*1024:
            raise ValueError('Seedance reference video exceeds 200 MB.')
        if min(width,height)>=300 and max(width,height)<=6000 and MIN_PIXELS<=width*height<=MAX_PIXELS:
            return source
        scale=max(math.sqrt(MIN_PIXELS/(width*height)),300/min(width,height))
        if width*height>MAX_PIXELS or max(width,height)>6000:
            scale=min(math.sqrt(MAX_PIXELS/(width*height)),6000/max(width,height))
        target_width=math.ceil(width*scale/2)*2
        target_height=math.ceil(height*scale/2)*2
        if not MIN_PIXELS<=target_width*target_height<=MAX_PIXELS:
            raise ValueError('Cannot resize this reference within Seedance pixel limits without changing framing.')
        target=folder/f'replicate-upload-video-{index}.mp4'
        with av.open(str(target),'w',options={'movflags':'+faststart'}) as out:
            stream=out.add_stream('libx264',rate=rate)
            stream.width=target_width;stream.height=target_height;stream.pix_fmt='yuv420p'
            stream.time_base=video.time_base;stream.options={'crf':'18','preset':'fast'}
            audio=out.add_stream_from_template(inp.streams.audio[0]) if inp.streams.audio else None
            for frame in inp.decode(video=0):
                resized=frame.reformat(width=target_width,height=target_height,format='yuv420p')
                for packet in stream.encode(resized):out.mux(packet)
            for packet in stream.encode():out.mux(packet)
            # Copy embedded pitched audio packets without encoding or changing timing.
            with av.open(str(source)) as audio_input:
                if audio:
                    for packet in audio_input.demux(audio=0):
                        if packet.dts is not None:packet.stream=audio;out.mux(packet)
    (folder/f'replicate-upload-video-{index}.json').write_text(json.dumps({
        'source':source.name,'upload':target.name,'original_dimensions':[width,height],
        'upload_dimensions':[target_width,target_height],'fps':float(rate),
        'duration':duration,'method':'Resize full frame; copy embedded audio packets; approved preparation unchanged.'},indent=2))
    return target
