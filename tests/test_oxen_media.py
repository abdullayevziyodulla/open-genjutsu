import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import oxen_media as media


def response(data=None, status=200, content=b'video'):
    result=Mock(status_code=status, headers={'Content-Type':'video/mp4'})
    result.json.return_value=data
    result.iter_content.return_value=[content]
    result.__enter__=Mock(return_value=result)
    result.__exit__=Mock(return_value=False)
    return result


class MediaTests(unittest.TestCase):
    def test_chunk_upload_uses_returned_workspace_id_and_exact_slices(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'clip.mp4';content=b'v'*(1024*1024+7);path.write_bytes(content)
            created=response({'workspace':{'id':'server-workspace'}})
            repo=self.repo().json()['repository']
            with patch.object(media,'credential',return_value='SECRET'),patch.object(media.requests,'put',side_effect=[created,response(),response()]) as put,patch.object(media.requests,'post',return_value=response()) as post:
                media.upload_chunks(path,'https://hub.oxen.ai/api/repos/user/private','main/genjustsu/clip.mp4',repo)
                chunks=put.call_args_list[1:]
                self.assertEqual(b''.join(call.kwargs['data'] for call in chunks),content)
                self.assertEqual([call.kwargs['params']['offset'] for call in chunks],[0,1024*1024])
                self.assertEqual(post.call_args_list[1].kwargs['json']['workspace_id'],'server-workspace')
                self.assertIn('/server-workspace/merge/main',post.call_args.args[0])

    def repo(self, public=False):
        return response({'repository':{'is_public':public,'visibility':'public' if public else 'private',
                         'default_branch':'main','latest_commit':{'author':'user','email':'user@example.com'}}})

    def test_existing_file_signed_download_without_credential(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'clip.mp4';path.write_bytes(b'video')
            signed=response({'url':'https://hub.oxen.ai/api/file?oxen_signature=signed'})
            with patch.object(media,'setting',return_value='user/private'),patch.object(media,'credential',return_value='SECRET'),patch.object(media.requests,'get',side_effect=[self.repo(),response(),signed,response()]) as get,patch.object(media.requests,'put') as put:
                media.upload_file(path)
                put.assert_not_called()
                self.assertNotIn('headers',get.call_args.kwargs)
                saved=json.loads(path.with_name('clip.mp4.oxen-storage.json').read_text())
                self.assertEqual(saved['sha256'],hashlib.sha256(b'video').hexdigest())

    def test_missing_file_uploaded_before_signing(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'clip.mp4';path.write_bytes(b'video')
            signed=response({'url':'https://hub.oxen.ai/api/file?oxen_signature=signed'})
            with patch.object(media,'setting',return_value='user/private'),patch.object(media,'credential',return_value='SECRET'),patch.object(media.requests,'get',side_effect=[self.repo(),response(status=404),signed,response()]),patch.object(media.requests,'put',return_value=response()) as put:
                media.upload_file(path)
                put.assert_called_once()
                self.assertEqual(put.call_args.kwargs['data']['name'],'user')

    def test_public_storage_rejected_before_upload(self):
        with patch.object(media,'setting',return_value='user/public'),patch.object(media,'credential',return_value='SECRET'),patch.object(media.requests,'get',return_value=self.repo(True)),patch.object(media.requests,'put') as put:
            with self.assertRaises(media.MediaLinkError):media.upload_file(Path('unused.mp4'))
            put.assert_not_called()

    def test_different_download_bytes_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'clip.mp4';path.write_bytes(b'video')
            signed=response({'url':'https://hub.oxen.ai/api/file?oxen_signature=signed'})
            with patch.object(media,'setting',return_value='user/private'),patch.object(media,'credential',return_value='SECRET'),patch.object(media.requests,'get',side_effect=[self.repo(),response(),signed,response(content=b'wrong')]):
                with self.assertRaises(media.MediaLinkError):media.upload_file(path)
                self.assertFalse(path.with_name('clip.mp4.oxen-storage.json').exists())
