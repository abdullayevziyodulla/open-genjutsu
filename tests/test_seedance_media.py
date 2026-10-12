import hashlib
import json
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

import av
import numpy as np
from seedance_media import upload_video


class SeedanceMediaTests(unittest.TestCase):
    def video(self,path,width=576,height=576,rate=24,seconds=4):
        with av.open(str(path),'w') as out:
            v=out.add_stream('libx264',rate=rate);v.width=width;v.height=height;v.pix_fmt='yuv420p'
            a=out.add_stream('aac',rate=44100);a.layout='stereo'
            for i in range(rate*seconds):
                f=av.VideoFrame.from_ndarray(np.full((height,width,3),i%255,dtype=np.uint8),format='rgb24')
                f.pts=i;f.time_base=Fraction(1,rate)
                for packet in v.encode(f):out.mux(packet)
            for packet in v.encode():out.mux(packet)
            samples=np.zeros((2,44100*seconds),dtype=np.float32)
            for i in range(0,samples.shape[1],4096):
                f=av.AudioFrame.from_ndarray(np.ascontiguousarray(samples[:,i:i+4096]),format='fltp',layout='stereo')
                f.sample_rate=44100;f.pts=i
                for packet in a.encode(f):out.mux(packet)
            for packet in a.encode():out.mux(packet)

    def test_576_square_resizes_to_640_without_touching_approved_source_or_audio(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);source=folder/'seedance-input.mp4';self.video(source)
            original=hashlib.sha256(source.read_bytes()).hexdigest()
            target=upload_video(source,folder)
            self.assertNotEqual(source,target)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),original)
            with av.open(str(target)) as result:
                v=result.streams.video[0]
                self.assertEqual((v.width,v.height),(640,640))
                self.assertEqual(v.duration*v.time_base,4)
                self.assertEqual(sum(1 for _ in result.decode(video=0)),96)
            def packets(path):
                with av.open(str(path)) as c:
                    return [(bytes(p),p.pts,p.dts,p.time_base) for p in c.demux(audio=0) if p.dts is not None]
            self.assertEqual(packets(source),packets(target))
            self.assertEqual(json.loads((folder/'replicate-upload-video-1.json').read_text())['upload_dimensions'],[640,640])

    def test_valid_640_video_does_not_encode(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);source=folder/'valid.mp4';self.video(source,width=640,height=640)
            self.assertEqual(upload_video(source,folder),source)

    def test_invalid_fps_is_rejected_before_upload(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);source=folder/'invalid.mp4';self.video(source,rate=12)
            with self.assertRaisesRegex(ValueError,'frame rate'):upload_video(source,folder)
