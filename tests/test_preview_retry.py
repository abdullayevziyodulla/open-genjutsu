import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mask_review import fingerprint,review,require_approved
from preview_retry import prepare_retry,submit_retry
from generation_status import snapshot


class PreviewRetryTests(unittest.TestCase):
    def fixture(self,root):
        source=Path(root)/('a'*32);source.mkdir()
        for name in ['original.mp4','depth.mp4','mask.mp4','composite-silent.mp4',
                     'seedance-input.mp4','upload.mp4','audio-manifest.json','replicate-reference-1.jpg']:
            (source/name).write_bytes(name.encode())
        review(source,True,'User reviewed the full clip',fingerprint(source))
        generation={'provider':'replicate','prompt':'Exact approved prompt',
                    'local_videos':['seedance-input.mp4'],'local_images':['replicate-reference-1.jpg']}
        (source/'generation.json').write_text(json.dumps(generation))
        (source/'provider-status.json').write_text('{"status":"failed"}')
        for name in ['seedance-response.json','submission-intent.json','seedance-result.mp4']:
            (source/name).write_text('old request')
        return source

    def test_reuses_approved_assets_preserves_failure_and_links_once(self):
        with tempfile.TemporaryDirectory() as root:
            source=self.fixture(root)
            target,created=prepare_retry(source)
            self.assertTrue(created);require_approved(target)
            self.assertEqual(fingerprint(source),fingerprint(target))
            self.assertEqual((target/'seedance-input.mp4').read_bytes(),(source/'seedance-input.mp4').read_bytes())
            self.assertFalse((target/'submission-intent.json').exists())
            self.assertFalse((target/'seedance-result.mp4').exists())
            self.assertTrue((source/'submission-intent.json').exists())
            self.assertEqual(prepare_retry(source),(target,False))
            self.assertEqual(snapshot(source)['retry_job'],target.name)

    def test_no_retry_for_running_or_ambiguous_prediction(self):
        for state in ['starting','processing','succeeded',None]:
            with self.subTest(state=state),tempfile.TemporaryDirectory() as root:
                source=self.fixture(root)
                (source/'provider-status.json').write_text(json.dumps({'status':state}))
                with self.assertRaises(ValueError):prepare_retry(source)
                self.assertFalse((source/'retry-preview.json').exists())

    def test_retry_uses_exact_prompt_without_appending_instructions(self):
        with tempfile.TemporaryDirectory() as root:
            target,_=prepare_retry(self.fixture(root))
            with patch('replicate_seedance.submit',return_value='prediction') as submit:
                self.assertEqual(submit_retry(target),'prediction')
                self.assertEqual(submit.call_args.args[1],'Exact approved prompt')
                self.assertTrue(submit.call_args.kwargs['prompt_is_final'])

    def test_uploading_is_active_only_when_worker_is_live(self):
        with tempfile.TemporaryDirectory() as root:
            folder=Path(root)
            state={'state':'running','stage':'submission','status':'Uploading references'}
            self.assertEqual(snapshot(folder,state)['phase'],'submitting')
            self.assertTrue(snapshot(folder,state)['active'])
            (folder/'status.json').write_text(json.dumps(state))
            self.assertFalse(snapshot(folder)['active'])
            (folder/'submission-intent.json').write_text('{"state":"submitting"}')
            self.assertEqual(snapshot(folder)['phase'],'unknown')

    def test_sensitive_input_has_no_unchanged_retry_but_can_open_unsubmitted_revision(self):
        with tempfile.TemporaryDirectory() as root:
            source=self.fixture(root)
            (source/'provider-status.json').write_text('{"status":"failed","error":"Flagged as sensitive (E005)"}')
            self.assertEqual(snapshot(source)['phase'],'blocked')
            with self.assertRaisesRegex(ValueError,'Change the reference'):prepare_retry(source)
            target,created=prepare_retry(source,revise=True)
            self.assertTrue(created);require_approved(target)
            self.assertFalse((target/'submission-intent.json').exists())
            self.assertFalse(snapshot(target)['attempted'])
            self.assertIn('E005',snapshot(target)['message'])
            self.assertEqual(prepare_retry(source,revise=True),(target,False))

    def test_revised_job_cannot_submit_unchanged_rejected_inputs(self):
        import replicate_seedance as bridge
        with tempfile.TemporaryDirectory() as root:
            source=self.fixture(root)
            generation=json.loads((source/'generation.json').read_text())
            generation['prompt']=bridge.build_prompt(source,'Exact approved prompt')
            (source/'generation.json').write_text(json.dumps(generation))
            target,_=prepare_retry(source,revise=True)
            with patch.object(bridge,'credential',return_value='test'),patch.object(bridge,'upload_file') as upload,patch.object(bridge,'queue') as queue:
                with self.assertRaisesRegex(ValueError,'same input'):
                    bridge.submit(target,'Exact approved prompt',target/'replicate-reference-1.jpg')
                upload.assert_not_called();queue.assert_not_called()
