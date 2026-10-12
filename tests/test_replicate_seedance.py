import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests
import replicate_seedance as bridge
import seedance_bridge


class ReplicateSeedanceTests(unittest.TestCase):
    def prepared(self, folder):
        for name in ['audio-manifest.json', 'seedance-input.mp4', 'upload.mp4', 'reference.png']:
            (folder / name).write_bytes(b'fixture')

    def test_image_preview_uses_replicate_schema_and_no_enhancor(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            self.prepared(folder)
            response = Mock(ok=True)
            response.json.return_value = {'id': 'prediction-one', 'status': 'starting'}
            with patch.object(bridge, 'require_approved'), patch.object(bridge, 'credential', return_value='test'), \
                 patch.object(bridge, 'validate_duration'), patch.object(bridge,'upload_video',side_effect=lambda p,f,i:p), \
                 patch.object(bridge, 'upload_file', return_value='https://example.com/file'), \
                 patch.object(bridge.requests, 'post', return_value=response) as post:
                ident = bridge.submit(folder, 'Replace @Video1 using @Image1', folder/'reference.png')
                self.assertEqual(ident, 'prediction-one')
                self.assertEqual(post.call_args.args[0], bridge.API+'/models/bytedance/seedance-2.5/predictions')
                payload = post.call_args.kwargs['json']['input']
                self.assertEqual(payload['resolution'], '480p')
                self.assertEqual(payload['duration'], -1)
                self.assertEqual(payload['aspect_ratio'], 'adaptive')
                self.assertEqual(len(payload['reference_videos']), 1)
                self.assertEqual(len(payload['reference_images']), 1)
                self.assertNotIn('is_draft', payload)
                self.assertNotIn('webhook_url', payload)
                self.assertNotIn('@Video1', payload['prompt'])
                self.assertIn('[Video1]', payload['prompt'])
                with self.assertRaises(ValueError):
                    bridge.submit(folder, 'Retry', folder/'reference.png')
                self.assertEqual(post.call_count, 1)

    def test_ambiguous_submission_cannot_be_billed_twice(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            with patch.object(bridge, 'credential', return_value='test'), \
                 patch.object(bridge.requests, 'post', side_effect=requests.Timeout) as post:
                with self.assertRaises(RuntimeError):
                    bridge.queue(folder, {'input': {}}, 'seedance-response.json')
                with self.assertRaises(ValueError):
                    bridge.queue(folder, {'input': {}}, 'seedance-response.json')
                self.assertEqual(post.call_count, 1)

    def test_recovery_routes_by_saved_provider(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder/'seedance-response.json').write_text(json.dumps({'provider':'replicate','requestId':'saved'}))
            with patch.object(bridge, 'wait_and_finish') as collect:
                seedance_bridge.wait_and_finish(folder, 'saved')
                collect.assert_called_once()

    def test_finished_prediction_downloads_and_restores_audio(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            prediction = Mock()
            prediction.json.return_value = {'status':'succeeded','output':'https://replicate.delivery/result.mp4'}
            media = Mock(content=b'video-result')
            with patch.object(bridge, 'credential', return_value='test'), \
                 patch.object(bridge.requests, 'get', side_effect=[prediction,media]) as get, \
                 patch.object(bridge, 'finish_preview') as restore:
                bridge.wait_and_finish(folder, 'saved')
                self.assertEqual((folder/'seedance-result.mp4').read_bytes(), b'video-result')
                restore.assert_called_once_with(folder/'seedance-result.mp4',folder)
                self.assertEqual(get.call_args_list[0].args[0], bridge.API+'/predictions/saved')

    def test_720p_is_new_prediction_with_fresh_uploads_and_preserved_preview(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            self.prepared(folder)
            (folder/'final-preview.mp4').write_bytes(b'preview')
            (folder/'generation.json').write_text(json.dumps({'provider':'replicate',
                'local_videos':['seedance-input.mp4'],'local_images':['reference.png']}))
            (folder/'seedance-request.json').write_text(json.dumps({'input':{
                'resolution':'480p','prompt':'Exact reviewed prompt','reference_videos':['old'], 'reference_images':['old']}}))
            response = Mock(ok=True)
            response.json.return_value = {'id':'720p-new'}
            with patch.object(bridge, 'require_approved') as approval, patch.object(bridge, 'validate_duration'), \
                 patch.object(bridge, 'credential', return_value='test'), patch.object(bridge,'upload_video',side_effect=lambda p,f,i:p), \
                 patch.object(bridge, 'upload_file', return_value='https://example.com/fresh') as upload, \
                 patch.object(bridge.requests, 'post', return_value=response) as post:
                self.assertEqual(bridge.submit_hd(folder), '720p-new')
                approval.assert_called_once_with(folder)
                self.assertEqual(upload.call_count, 2)
                payload=post.call_args.kwargs['json']['input']
                self.assertEqual(payload['resolution'],'720p')
                self.assertEqual(payload['prompt'],'Exact reviewed prompt')
                self.assertEqual(payload['reference_videos'],['https://example.com/fresh'])
                self.assertEqual((folder/'final-preview.mp4').read_bytes(),b'preview')
                self.assertEqual((folder/'hd/upload.mp4').read_bytes(),b'fixture')
                with self.assertRaises(ValueError): bridge.submit_hd(folder)
                self.assertEqual(post.call_count,1)

    def test_video_identity_uses_video_two_and_image_one_for_second_character(self):
        with tempfile.TemporaryDirectory() as directory:
            prompt=bridge.build_prompt(Path(directory),'Use @Video1',True,True)
            self.assertIn('[Video2] supplies only the replacement visual identity',prompt)
            self.assertIn('[Image1] supplies the second character identity',prompt)

    def test_failed_prediction_does_not_restore_or_resubmit(self):
        with tempfile.TemporaryDirectory() as directory:
            response=Mock()
            response.json.return_value={'status':'failed','error':'provider failure'}
            with patch.object(bridge,'credential',return_value='test'), \
                 patch.object(bridge.requests,'get',return_value=response), \
                 patch.object(bridge.requests,'post') as post, patch.object(bridge,'finish_preview') as restore:
                with self.assertRaises(RuntimeError):bridge.wait_and_finish(directory,'saved')
                post.assert_not_called()
                restore.assert_not_called()
