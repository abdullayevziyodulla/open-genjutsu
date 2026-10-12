import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from generation_status import snapshot
import replicate_seedance


class GenerationStatusTests(unittest.TestCase):
    def saved(self,folder,state):
        data={'id':'saved-prediction','provider':'replicate','status':state,
              'created_at':'2026-10-10T06:30:51Z','urls':{'get':'https://example.com/private-url'},
              'input':{'reference_images':['https://example.com/private-reference']}}
        (folder/'seedance-response.json').write_text(json.dumps(data))
        return data

    def test_idle_and_preparation_are_not_video_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            state=snapshot(directory,{'state':'running','status':'Preparing depth'})
            self.assertEqual(state['phase'],'idle')
            self.assertFalse(state['active'])
            self.assertFalse(state['attempted'])

    def test_accepted_prediction_is_queued_and_locks_submission(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);self.saved(folder,'starting')
            state=snapshot(folder)
            self.assertEqual(state['phase'],'queued')
            self.assertTrue(state['active'])
            self.assertTrue(state['attempted'])
            self.assertEqual(state['prediction_url'],'https://replicate.com/p/saved-prediction')
            self.assertNotIn('private-reference',json.dumps(state))
            self.assertNotIn('private-url',json.dumps(state))

    def test_processing_and_finishing_remain_active_until_local_output_exists(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);data=self.saved(folder,'starting')
            data['status']='processing'
            (folder/'provider-status.json').write_text(json.dumps(data))
            self.assertEqual(snapshot(folder)['phase'],'generating')
            data['status']='succeeded';data['completed_at']='2026-10-10T06:30:58Z'
            (folder/'provider-status.json').write_text(json.dumps(data))
            self.assertEqual(snapshot(folder)['phase'],'finishing')
            (folder/'final-preview.mp4').write_bytes(b'finished')
            state=snapshot(folder)
            self.assertEqual(state['phase'],'done')
            self.assertFalse(state['active'])

    def test_provider_failure_is_terminal_and_visible_even_with_stale_local_state(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);data=self.saved(folder,'starting')
            data.update(status='failed',error='Invalid input (E006)',completed_at='2026-10-10T06:30:58Z')
            (folder/'provider-status.json').write_text(json.dumps(data))
            state=snapshot(folder,{'state':'running','status':'Generating'})
            self.assertEqual(state['phase'],'failed')
            self.assertFalse(state['active'])
            self.assertIn('E006',state['message'])
            self.assertEqual(state['elapsed_seconds'],7)
            self.assertTrue(state['attempted'])

    def test_ambiguous_submission_does_not_claim_queued_or_enable_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)
            (folder/'submission-intent.json').write_text('{"state":"submitting"}')
            state=snapshot(folder)
            self.assertEqual(state['phase'],'unknown')
            self.assertTrue(state['attempted'])
            self.assertFalse(state['active'])

    def test_upload_sets_the_media_type_expected_by_replicate(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)
            response=Mock();response.json.return_value={'urls':{'get':'https://api.replicate.com/v1/files/test'}}
            with patch.object(replicate_seedance,'headers',return_value={}),patch.object(replicate_seedance.requests,'post',return_value=response) as post:
                for name,mime in [('input.mp4','video/mp4'),('reference.jpg','image/jpeg')]:
                    path=folder/name;path.write_bytes(b'fixture')
                    replicate_seedance.upload_file(path)
                    part=post.call_args.kwargs['files']['content']
                    self.assertEqual(part[0],name)
                    self.assertEqual(part[2],mime)
