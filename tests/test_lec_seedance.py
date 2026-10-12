import hashlib
import json
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from unittest.mock import Mock, patch

import av
import numpy as np
import requests
from fastapi.testclient import TestClient

import lec_seedance as lec
from audio_workflow import finish_preview
from generation_status import snapshot
from mask_review import fingerprint, review, require_approved


def video(path, seconds, audio=False):
    rate = 24
    with av.open(str(path), 'w') as out:
        stream = out.add_stream('libx264', rate=rate)
        stream.width = stream.height = 64
        stream.pix_fmt = 'yuv420p'
        audio_stream = out.add_stream('aac', rate=44100) if audio else None
        if audio_stream:audio_stream.layout = 'stereo'
        for i in range(round(seconds * rate)):
            frame = av.VideoFrame.from_ndarray(np.full((64, 64, 3), i % 255, np.uint8), format='rgb24')
            frame.pts, frame.time_base = i, Fraction(1, rate)
            for packet in stream.encode(frame):
                out.mux(packet)
        for packet in stream.encode():
            out.mux(packet)
        if audio:
            stream = audio_stream
            samples = np.zeros((2, round(seconds * 44100)), np.float32)
            for i in range(0, samples.shape[1], 4096):
                frame = av.AudioFrame.from_ndarray(np.ascontiguousarray(samples[:, i:i+4096]), format='fltp', layout='stereo')
                frame.sample_rate, frame.pts = 44100, i
                for packet in stream.encode(frame):
                    out.mux(packet)
            for packet in stream.encode():
                out.mux(packet)


class LecTests(unittest.TestCase):
    def fixture(self, directory):
        folder = Path(directory)
        for name in ['original.mp4', 'depth.mp4', 'mask.mp4', 'composite-silent.mp4']:
            (folder/name).write_bytes(name.encode())
        video(folder/'seedance-input.mp4', 4.375, audio=True)
        (folder/'audio-manifest.json').write_text('{}')
        (folder/'portrait.jpg').write_bytes(b'portrait')
        review(folder, True, 'User reviewed the full clip', fingerprint(folder))
        return folder

    def approve_plan(self, folder):
        payload, videos, images = lec.plan(folder, 'Replace the person.', folder/'portrait.jpg')
        (folder/'lec-plan-review.json').write_text(json.dumps({'hash':lec.plan_hash(payload, videos, images)}))
        return payload

    def test_reference_schema_embedded_audio_and_integer_duration(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = self.fixture(directory)
            payload, videos, images = lec.plan(folder, 'Replace the person.', folder/'portrait.jpg')
            self.assertEqual(payload['model'], 'lec-mj-seedance-2-5-bd-720p')
            self.assertEqual(payload['duration'], 5)
            self.assertEqual(payload['aspect_ratio'], '1:1')
            self.assertIn('@Video1', payload['prompt'])
            self.assertIn('@Image1', payload['prompt'])
            self.assertEqual(videos, [folder/'seedance-input.mp4'])
            self.assertEqual(images, [folder/'portrait.jpg'])
            self.assertNotIn('is_draft', payload)
            self.assertNotIn('pass_faces', payload)

    def test_unreviewed_or_changed_request_cannot_start_paid_upload(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = self.fixture(directory)
            with patch.object(lec, 'credential', return_value='test'), patch.object(lec, 'upload_file') as upload:
                with self.assertRaisesRegex(ValueError, 'exact Lec prompt'):
                    lec.submit(folder, 'Replace the person.', folder/'portrait.jpg')
                self.approve_plan(folder)
                (folder/'portrait.jpg').write_bytes(b'changed')
                with self.assertRaisesRegex(ValueError, 'exact Lec prompt'):
                    lec.submit(folder, 'Replace the person.', folder/'portrait.jpg')
                upload.assert_not_called()
                self.assertFalse((folder/'submission-intent.json').exists())

    def test_native_upload_mime_cache_and_uncertain_upload_reuses_idempotency_key(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);path=folder/'reference.jpg';path.write_bytes(b'portrait')
            response=Mock();response.json.return_value={'data':{'url':'https://signed.example/private?a=1', 'expires_at':'2099-01-01T00:00:00Z'}}
            with patch.object(lec, 'headers', return_value={}), patch.object(lec.requests, 'post', side_effect=[requests.Timeout(),response]) as post:
                with self.assertRaises(requests.Timeout):lec.upload_file(folder,path)
                first_key=post.call_args.kwargs['headers']['Idempotency-Key']
                self.assertEqual(lec.upload_file(folder,path),'https://signed.example/private?a=1')
                self.assertEqual(post.call_args.kwargs['headers']['Idempotency-Key'],first_key)
                self.assertEqual(post.call_args.kwargs['files']['file'][2],'image/jpeg')
                self.assertEqual(lec.upload_file(folder,path),'https://signed.example/private?a=1')
                self.assertEqual(post.call_count,2)

    def test_submit_saved_id_and_duplicate_guard_cover_uploads(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=self.fixture(directory);self.approve_plan(folder)
            response=Mock(ok=True);response.json.return_value={'id':'lec-one','status':'queued'}
            with patch.object(lec,'credential',return_value='test'),patch.object(lec,'upload_file',return_value='https://signed.example/asset') as upload,patch.object(lec.requests,'post',return_value=response) as post:
                self.assertEqual(lec.submit(folder,'Replace the person.',folder/'portrait.jpg',status=lambda _:None),'lec-one')
                self.assertEqual(upload.call_count,2)
                self.assertEqual(post.call_args.kwargs['json']['audios'],[])
                self.assertEqual(json.loads((folder/'generation.json').read_text())['resolution'],'720p')
                with self.assertRaisesRegex(ValueError,'already attempted'):
                    lec.submit(folder,'Replace the person.',folder/'portrait.jpg')
                self.assertEqual(upload.call_count,2)
                self.assertEqual(post.call_count,1)

    def test_ambiguous_post_is_not_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=self.fixture(directory);self.approve_plan(folder)
            with patch.object(lec,'credential',return_value='test'),patch.object(lec,'upload_file',return_value='https://signed.example/asset'),patch.object(lec.requests,'post',side_effect=requests.Timeout()) as post:
                with self.assertRaisesRegex(RuntimeError,'duplicate charges'):
                    lec.submit(folder,'Replace the person.',folder/'portrait.jpg',status=lambda _:None)
                with self.assertRaises(ValueError):lec.submit(folder,'Replace the person.',folder/'portrait.jpg')
                self.assertEqual(post.call_count,1)
                self.assertEqual(snapshot(folder)['phase'],'unknown')

    def test_provider_progress_unix_times_and_unknown_state(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)
            (folder/'generation.json').write_text('{"provider":"lec","request_id":"lec-one","resolution":"720p"}')
            (folder/'provider-status.json').write_text('{"status":"in_progress","progress":42,"created_at":100,"completed_at":107}')
            state=snapshot(folder)
            self.assertEqual(state['phase'],'generating');self.assertEqual(state['progress'],42)
            self.assertEqual(state['elapsed_seconds'],7);self.assertIn('Lec',state['message'])
            (folder/'provider-status.json').write_text('{"status":"unknown"}')
            self.assertEqual(snapshot(folder)['phase'],'unknown')
            self.assertFalse(snapshot(folder)['active'])

    def test_collection_keeps_signed_query_and_never_leaks_key_to_output_host(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)
            task=Mock(status_code=200);task.json.return_value={'status':'completed','url':'https://upstream.example/result?signature=keep'}
            media=Mock(content=b'result')
            with patch.object(lec,'headers',return_value={'Authorization':'Bearer SECRET'}),patch.object(lec.requests,'get',side_effect=[task,media]) as get,patch.object(lec.requests,'post') as post,patch.object(lec,'align_result',return_value=folder/'seedance-result.mp4'),patch.object(lec,'finish_preview'):
                lec.wait_and_finish(folder,'task/id',status=lambda _:None)
                self.assertTrue(get.call_args_list[0].args[0].endswith('/task%2Fid'))
                self.assertEqual(get.call_args_list[1].args[0],'https://upstream.example/result?signature=keep')
                self.assertEqual(get.call_args_list[1].kwargs['headers'],{})
                post.assert_not_called()

    def test_saved_provider_routes_collection_even_after_configuration_changes(self):
        import seedance_bridge
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);(folder/'generation.json').write_text('{"provider":"lec"}')
            with patch.object(lec,'wait_and_finish',return_value='collected') as collect,patch.object(seedance_bridge,'setting',return_value='replicate'):
                self.assertEqual(seedance_bridge.wait_and_finish(folder,'saved'),'collected')
                self.assertEqual(collect.call_args.args[1],'saved')

    def test_rounding_tail_trim_keeps_full_original_audio_packets_and_speed(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);video(folder/'upload.mp4',4.375,audio=True);video(folder/'seedance-result.mp4',5)
            raw_hash=hashlib.sha256((folder/'seedance-result.mp4').read_bytes()).hexdigest()
            result=finish_preview(lec.align_result(folder),folder)
            self.assertAlmostEqual(lec.media_seconds(result),4.375,places=3)
            self.assertEqual(hashlib.sha256((folder/'seedance-result.mp4').read_bytes()).hexdigest(),raw_hash)
            def packets(path):
                with av.open(str(path)) as c:return [(bytes(p),p.pts,p.dts,p.time_base) for p in c.demux(audio=0) if p.dts is not None]
            self.assertEqual(packets(result),packets(folder/'upload.mp4'))
            self.assertEqual(json.loads((folder/'duration-adjustment.json').read_text())['speed'],'unchanged')

    def test_existing_preparation_reused_without_stale_plan_or_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/('a'*32);source.mkdir();self.fixture(source);self.approve_plan(source)
            (source/'submission-intent.json').write_text('{"provider":"replicate"}')
            target=lec.prepare_job(source);require_approved(target)
            self.assertEqual((source/'seedance-input.mp4').read_bytes(),(target/'seedance-input.mp4').read_bytes())
            self.assertFalse((target/'lec-plan-review.json').exists());self.assertFalse((target/'submission-intent.json').exists())
            self.assertTrue((source/'submission-intent.json').exists())

    def test_key_configuration_is_local_and_response_never_contains_secret(self):
        import app
        client=TestClient(app.app)
        with patch('config.save_setting') as save:
            response=client.post('/configuration/lec',data={'api_key':'FAKE_SECRET'},headers={'Origin':'https://unrelated.example'})
            self.assertEqual(response.status_code,403);save.assert_not_called()
            response=client.post('/configuration/lec',data={'api_key':'FAKE_SECRET'})
            self.assertEqual(response.status_code,200);self.assertNotIn('FAKE_SECRET',response.text)
            self.assertEqual(save.call_args_list[0].args,('LEC_API_KEY','FAKE_SECRET'))

    def test_local_plan_and_submission_hash_gate_run_before_provider_upload(self):
        import app
        with tempfile.TemporaryDirectory() as directory:
            runs=Path(directory);ident='b'*32;folder=runs/ident;folder.mkdir();self.fixture(folder)
            client=TestClient(app.app)
            with patch.object(app,'RUNS',runs),patch.object(app,'jobs',{}),patch('config.setting',side_effect=lambda name,default='':'lec' if name=='GENERATION_PROVIDER' else 'fake'),patch.object(app.threading,'Thread') as thread,patch.object(lec.requests,'post') as external:
                request={'prompt':'Replace the person.'}
                files={'sirio':('portrait.jpg',b'portrait','image/jpeg')}
                response=client.post('/jobs/'+ident+'/lec-plan',data=request,files=files)
                self.assertEqual(response.status_code,200);external.assert_not_called()
                self.assertEqual(response.json()['upload_price_usd'],0.06)
                bad=client.post('/jobs/'+ident+'/seedance',data={**request,'reviewed_plan':'old-hash'},files=files)
                self.assertEqual(bad.status_code,409);thread.assert_not_called();external.assert_not_called()
                accepted=client.post('/jobs/'+ident+'/seedance',data={**request,'reviewed_plan':response.json()['hash']},files=files)
                self.assertEqual(accepted.status_code,200);thread.return_value.start.assert_called_once()
                external.assert_not_called()
                duplicate=client.post('/jobs/'+ident+'/seedance',data={**request,'reviewed_plan':response.json()['hash']},files=files)
                self.assertEqual(duplicate.status_code,409)


if __name__=='__main__':unittest.main()
