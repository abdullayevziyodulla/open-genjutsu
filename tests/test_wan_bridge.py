import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock,patch

import wan_bridge as wan
import replicate_seedance as replicate
from generation_status import snapshot


class WanTests(unittest.TestCase):
    def fixture(self,folder):
        (folder/'upload.mp4').write_bytes(b'original')
        (folder/'seedance-input.mp4').write_bytes(b'prepared')
        (folder/'reference.jpg').write_bytes(b'portrait')

    def test_submits_original_and_one_photo_to_wan_and_blocks_duplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);self.fixture(folder)
            response=Mock(ok=True);response.json.return_value={'id':'wan-one','status':'starting','model':wan.MODEL}
            with patch.object(wan,'require_approved'),patch.object(wan,'media',return_value=folder/'upload.mp4'),patch.object(wan,'upload_file',return_value='https://example.com/media') as upload,patch.object(replicate,'headers',return_value={}),patch.object(replicate.requests,'post',return_value=response) as post:
                ident=wan.submit(folder,'old prompt',folder/'reference.jpg')
                self.assertEqual(ident,'wan-one')
                self.assertEqual(post.call_args.args[0],replicate.API+'/models/'+wan.MODEL+'/predictions')
                payload=post.call_args.kwargs['json']['input']
                self.assertEqual(payload['resolution'],'480')
                self.assertFalse(payload['merge_audio'])
                self.assertNotIn('prompt',payload)
                self.assertEqual(upload.call_args_list[0].args[0],folder/'upload.mp4')
                self.assertEqual(json.loads((folder/'generation.json').read_text())['model'],wan.MODEL)
                self.assertEqual((folder/'seedance-input.mp4').read_bytes(),b'prepared')
                self.assertEqual(snapshot(folder)['engine'],'wan')
                with self.assertRaises(ValueError):wan.submit(folder,'',folder/'reference.jpg')
                self.assertEqual(post.call_count,1)

    def test_wan_720_routes_to_same_model_with_fresh_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);self.fixture(folder)
            (folder/'generation.json').write_text(json.dumps({'model':wan.MODEL,'local_images':['reference.jpg']}))
            (folder/'seedance-request.json').write_text('{"input":{"resolution":"480","merge_audio":false}}')
            (folder/'final-preview.mp4').write_bytes(b'preview')
            with patch.object(wan,'require_approved'),patch.object(wan,'media',return_value=folder/'upload.mp4'),patch.object(wan,'upload_file',return_value='https://example.com/fresh'),patch.object(wan,'queue',return_value='wan-hd') as queue:
                self.assertEqual(replicate.submit_hd(folder),'wan-hd')
                self.assertEqual(queue.call_args.kwargs['model'],wan.MODEL)
                self.assertEqual(queue.call_args.args[1]['input']['resolution'],'720')
                self.assertEqual((folder/'final-preview.mp4').read_bytes(),b'preview')

    def test_route_marks_uploading_before_thread_and_rejects_duplicate_request(self):
        import app
        from fastapi import UploadFile,HTTPException
        with tempfile.TemporaryDirectory() as directory:
            runs=Path(directory);ident='a'*32;folder=runs/ident;folder.mkdir()
            (folder/'audio-manifest.json').write_text('{}')
            with patch('config.setting',return_value='replicate'),patch.object(app,'RUNS',runs),patch.object(app,'jobs',{}),patch('mask_review.require_approved'),patch.object(app.threading,'Thread') as thread:
                result=app.seedance(ident,'',UploadFile(filename='reference.jpg',file=io.BytesIO(b'photo')),None,'wan')
                self.assertEqual(result['state'],'running')
                self.assertEqual(snapshot(folder,app.jobs[ident])['phase'],'submitting')
                with self.assertRaises(HTTPException) as caught:
                    app.seedance(ident,'',UploadFile(filename='reference.jpg',file=io.BytesIO(b'changed')),None,'wan')
                self.assertEqual(caught.exception.status_code,409)
                self.assertEqual((folder/'sirio-reference.jpg').read_bytes(),b'photo')
                thread.return_value.start.assert_called_once()

    def test_wan_selection_does_not_display_old_seedance_failure_as_current(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)
            (folder/'revision-source.json').write_text('{"provider_error":"Sensitive (E005)"}')
            (folder/'preferred-engine.json').write_text('{"engine":"wan"}')
            state=snapshot(folder)
            self.assertEqual(state['engine'],'wan');self.assertFalse(state['attempted'])
            self.assertIsNone(state['error']);self.assertIn('Wan 2.2',state['message'])
