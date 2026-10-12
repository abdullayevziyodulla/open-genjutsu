import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests
from fastapi.testclient import TestClient
from PIL import Image

import oxen_seedance as oxen
from generation_status import snapshot
import test_lec_seedance as fixtures


class OxenTests(unittest.TestCase):
    def fixture(self, directory):
        folder = fixtures.LecTests().fixture(directory)
        Image.new('RGB', (64, 64)).save(folder/'portrait.jpg')
        (folder/'audio-manifest.json').write_text('{"pitch_semitones":3}')
        self.approve(folder)
        return folder

    def approve(self, folder):
        payload, videos, images = oxen.plan(folder, 'Replace the person.', folder/'portrait.jpg')
        (folder/'oxen-plan-review.json').write_text(json.dumps({'hash':oxen.plan_hash(payload, videos, images)}))

    def test_draft_uses_prepared_input_embedded_audio_and_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=self.fixture(directory)
            payload,videos,images=oxen.plan(folder,'Replace the person.',folder/'portrait.jpg')
            self.assertEqual(videos,[folder/'seedance-input.mp4'])
            self.assertEqual(images,[folder/'portrait.jpg'])
            self.assertEqual(payload['omni_reference_task_type'],'edit')
            self.assertEqual(payload['duration'],'auto')
            self.assertEqual(payload['resolution'],'480p')
            self.assertTrue(payload['draft'])
            self.assertFalse(payload['generate_audio'])
            self.assertIn('@Video1',payload['prompt']);self.assertIn('@Image1',payload['prompt'])
            self.assertNotIn('input_audios',payload)
            preview=oxen.preview(folder,'Replace the person.',folder/'portrait.jpg')
            self.assertFalse(preview['generate_audio'])
            self.assertEqual(preview['price_usd'],0.56)

    def test_changed_prompt_is_blocked_before_upload_or_price_check(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=self.fixture(directory)
            with patch.object(oxen,'preflight') as preflight,patch.object(oxen,'upload_file') as upload:
                with self.assertRaisesRegex(ValueError,'exact Oxen prompt'):
                    oxen.submit(folder,'A changed request.',folder/'portrait.jpg')
                preflight.assert_not_called();upload.assert_not_called()

    def test_one_submission_face_fields_and_duplicate_guard(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=self.fixture(directory)
            response=Mock(ok=True);response.json.return_value={'generations':[{'generation_id':'ox-one','status':'queued'}]}
            with patch.object(oxen,'preflight',return_value=0.111),patch.object(oxen,'upload_file',side_effect=['https://signed.example/video','https://signed.example/image']) as upload,patch.object(oxen,'headers',return_value={}),patch.object(oxen.requests,'post',return_value=response) as post:
                self.assertEqual(oxen.submit(folder,'Replace the person.',folder/'portrait.jpg',status=lambda _:None),'ox-one')
                body=post.call_args.kwargs['json']
                self.assertEqual(body['input_face_videos'],['https://signed.example/video'])
                self.assertEqual(body['input_face_images'],['https://signed.example/image'])
                self.assertNotIn('input_audios',body)
                with self.assertRaisesRegex(ValueError,'already attempted'):
                    oxen.submit(folder,'Replace the person.',folder/'portrait.jpg')
                self.assertEqual(upload.call_count,2);self.assertEqual(post.call_count,1)

    def test_uncertain_post_cannot_submit_again(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=self.fixture(directory)
            with patch.object(oxen,'preflight',return_value=0.111),patch.object(oxen,'upload_file',return_value='https://signed.example/asset'),patch.object(oxen,'headers',return_value={}),patch.object(oxen.requests,'post',side_effect=requests.Timeout()) as post:
                with self.assertRaisesRegex(RuntimeError,'duplicate generation charges'):
                    oxen.submit(folder,'Replace the person.',folder/'portrait.jpg',status=lambda _:None)
                with self.assertRaises(ValueError):oxen.submit(folder,'Replace the person.',folder/'portrait.jpg')
                self.assertEqual(post.call_count,1)
                self.assertEqual(snapshot(folder)['phase'],'unknown')

    def test_media_failure_is_distinct_from_an_uncertain_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=self.fixture(directory)
            with patch.object(oxen,'preflight',return_value=0.111),patch.object(oxen,'upload_file',side_effect=oxen.MediaLinkError('Storage link unreadable')),patch.object(oxen.requests,'post') as post:
                with self.assertRaises(oxen.MediaLinkError):
                    oxen.submit(folder,'Replace the person.',folder/'portrait.jpg',status=lambda _:None)
                post.assert_not_called()

                state=snapshot(folder)
                self.assertEqual(state['phase'],'not_submitted')
                self.assertFalse(state['active'])
                self.assertIsNone(state['prediction_id'])
                with self.assertRaises(ValueError):
                    oxen.submit(folder,'Replace the person.',folder/'portrait.jpg')
                post.assert_not_called()

    def test_explicit_recovery_preserves_audit_and_blocks_uncertain_attempts(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=self.fixture(directory)
            saved={'provider':'oxen','user_prompt':'Replace the person.','local_videos':['seedance-input.mp4'],'local_images':['portrait.jpg']}
            (folder/'generation.json').write_text(json.dumps(saved))
            marker=folder/'submission-intent.json'
            marker.write_text('{"provider":"oxen","state":"submitting"}')
            with self.assertRaises(ValueError):oxen.recover_upload(folder)
            marker.write_text('{"provider":"oxen","state":"not_submitted"}')
            (folder/'seedance-request.json').write_text('{}')
            with self.assertRaises(ValueError):oxen.recover_upload(folder)
            (folder/'seedance-request.json').unlink()
            prompt,references=oxen.recover_upload(folder)
            self.assertEqual(prompt,'Replace the person.')
            self.assertEqual(references,[folder/'portrait.jpg'])
            self.assertFalse(marker.exists())
            self.assertEqual(len(list((folder/'upload-attempts').glob('*/submission-intent.json'))),1)

    def test_price_increase_and_invalid_key_stop_before_upload(self):
        queue=Mock(status_code=200);model=Mock();model.json.return_value={'can_run_inference':True,'pricing':{'method':'per_video_output_second','cost_per_second_by_resolution':{'480p':0.2}}}
        with patch.object(oxen,'credential',return_value='fake'),patch.object(oxen.requests,'get',side_effect=[queue,model]),patch.object(oxen.requests,'post') as post:
            with self.assertRaisesRegex(ValueError,'increased'):oxen.preflight()
            post.assert_not_called()
        with patch.object(oxen,'credential',return_value='fake'),patch.object(oxen.requests,'get',return_value=Mock(status_code=401)):
            with self.assertRaisesRegex(ValueError,'accept this API key'):oxen.preflight()

    def test_polling_keeps_draft_id_and_signed_url_without_leaking_key(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=self.fixture(directory);(folder/'generation.json').write_text('{"provider":"oxen","draft":true}')
            task=Mock(status_code=200);task.json.return_value={'status':'succeeded','videos':[{'url':'https://upstream.example/out?signature=keep','draft_task_id':'draft-one','draft_expires_at':'2099-01-01T00:00:00Z'}]}
            media=Mock();media.__enter__=Mock(return_value=media);media.__exit__=Mock(return_value=False);media.iter_content.return_value=[b'video']
            with patch.object(oxen,'headers',return_value={'Authorization':'SECRET'}),patch.object(oxen.requests,'get',side_effect=[task,media]) as get,patch.object(oxen,'align_result',return_value=folder/'seedance-result.mp4'),patch.object(oxen,'finish_preview') as finish:
                oxen.wait_and_finish(folder,'ox-one',status=lambda _:None)
                self.assertEqual(get.call_args.args[0],'https://upstream.example/out?signature=keep')
                self.assertNotIn('headers',get.call_args.kwargs)
                self.assertEqual(json.loads((folder/'generation.json').read_text())['draft_task_id'],'draft-one')
                finish.assert_called_once()

    def test_final_reuses_provider_draft_id_only_and_preserves_source(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=self.fixture(directory);(folder/'upload.mp4').write_bytes(b'original');(folder/'final-preview.mp4').write_bytes(b'draft')
            (folder/'generation.json').write_text('{"provider":"oxen","draft_task_id":"upstream-draft","draft_expires_at":"2099-01-01T00:00:00Z"}')
            with patch.object(oxen,'credential',return_value='fake'),patch.object(oxen,'enqueue',return_value='final-one') as enqueue:
                self.assertEqual(oxen.submit_hd(folder),'final-one')
                self.assertEqual(enqueue.call_args.args[1],{'model':oxen.MODEL,'draft_task_id':'upstream-draft'})
                self.assertEqual((folder/'hd/upload.mp4').read_bytes(),b'original')
                self.assertEqual(json.loads((folder/'hd/generation.json').read_text())['resolution'],'1080p')
                with self.assertRaisesRegex(ValueError,'already attempted'):oxen.submit_hd(folder)

    def test_expired_draft_is_not_billed(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=self.fixture(directory);(folder/'final-preview.mp4').write_bytes(b'draft')
            (folder/'generation.json').write_text('{"draft_task_id":"expired","draft_expires_at":"2000-01-01T00:00:00Z"}')
            with patch.object(oxen.requests,'post') as post:
                with self.assertRaisesRegex(ValueError,'expired'):oxen.submit_hd(folder)
                post.assert_not_called()

    def test_progress_queue_times_and_error_message(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);(folder/'generation.json').write_text('{"provider":"oxen","request_id":"ox-one","resolution":"480p"}')
            (folder/'provider-status.json').write_text('{"status":"processing","enqueued_at":100,"completed_at":107}')
            state=snapshot(folder);self.assertIn('Oxen',state['message']);self.assertEqual(state['elapsed_seconds'],7)
            (folder/'provider-status.json').write_text('{"status":"failed","error_message":"insufficient credits"}')
            self.assertEqual(snapshot(folder)['error'],'insufficient credits')
            (folder/'provider-status.json').write_text('{"status":"cancelled"}')
            self.assertFalse(snapshot(folder)['active'])

    def test_local_key_form_rejects_external_origin_and_never_echoes_key(self):
        import app
        with patch('config.save_setting') as save:
            client=TestClient(app.app)
            denied=client.post('/configuration/oxen',data={'api_key':'FAKE_SECRET'},headers={'Origin':'https://unrelated.example'})
            self.assertEqual(denied.status_code,403);save.assert_not_called()
            accepted=client.post('/configuration/oxen',data={'api_key':'FAKE_SECRET'})
            self.assertEqual(accepted.status_code,200);self.assertNotIn('FAKE_SECRET',accepted.text)

    def test_local_review_hash_gates_worker_start(self):
        import app
        with tempfile.TemporaryDirectory() as directory:
            runs=Path(directory);ident='c'*32;folder=runs/ident;folder.mkdir();self.fixture(folder)
            files={'sirio':('portrait.jpg',(folder/'portrait.jpg').read_bytes(),'image/jpeg')}
            with patch.object(app,'RUNS',runs),patch.object(app,'jobs',{}),patch('config.setting',side_effect=lambda name,default='':'oxen' if name=='GENERATION_PROVIDER' else 'fake'),patch.object(app.threading,'Thread') as thread,patch.object(oxen.requests,'post') as post:
                client=TestClient(app.app);review=client.post('/jobs/'+ident+'/oxen-plan',data={'prompt':'Replace the person.'},files=files)
                self.assertEqual(review.status_code,200);post.assert_not_called()
                denied=client.post('/jobs/'+ident+'/seedance',data={'prompt':'Replace the person.','reviewed_plan':'stale'},files=files)
                self.assertEqual(denied.status_code,409);thread.assert_not_called()
                accepted=client.post('/jobs/'+ident+'/seedance',data={'prompt':'Replace the person.','reviewed_plan':review.json()['hash']},files=files)
                self.assertEqual(accepted.status_code,200);thread.return_value.start.assert_called_once();post.assert_not_called()

    def test_resume_uses_saved_oxen_provider(self):
        import seedance_bridge
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);(folder/'generation.json').write_text('{"provider":"oxen"}')
            with patch.object(oxen,'wait_and_finish',return_value='saved') as collect,patch.object(seedance_bridge,'setting',return_value='lec'):
                self.assertEqual(seedance_bridge.wait_and_finish(folder,'ox-one'),'saved')
                collect.assert_called_once()


if __name__=='__main__':unittest.main()
