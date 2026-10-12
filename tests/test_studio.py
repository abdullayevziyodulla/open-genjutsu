import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from fastapi.testclient import TestClient
import app

class StudioTests(unittest.TestCase):
    def test_preparation_preserves_selected_references_and_prompt(self):
        with tempfile.TemporaryDirectory() as directory:
            runs=Path(directory)
            with patch.object(app,'RUNS',runs),patch.object(app,'jobs',{}),patch.object(app.threading,'Thread') as worker:
                response=TestClient(app.app).post('/jobs',data={'generation_prompt':'Keep my facial proportions','engine':'seedance'},
                    files={'video':('source.mp4',b'source','video/mp4'),'sirio':('face.jpg',b'photo','image/jpeg')})
                self.assertEqual(response.status_code,200)
                folder=runs/response.json()['id']
                self.assertEqual((folder/'sirio-reference.jpg').read_bytes(),b'photo')
                self.assertEqual(json.loads((folder/'pending-creative.json').read_text())['prompt'],'Keep my facial proportions')
                worker.return_value.start.assert_called_once()

    def test_cross_origin_paid_submission_blocked_before_work(self):
        with patch.object(app.threading,'Thread') as worker:
            response=TestClient(app.app).post('/jobs',headers={'Origin':'https://unrelated.example'})
            self.assertEqual(response.status_code,403)
            worker.assert_not_called()

    def test_settings_validate_all_values_before_saving_and_hide_secrets(self):
        with patch('config.save_setting') as save,patch.object(app,'jobs',{}),patch.object(app,'hd_jobs',{}):
            client=TestClient(app.app)
            response=client.post('/configuration/settings',data={'provider':'oxen','replicate_token':'FAKE_TOKEN','storage_repo':'bad/path/extra'})
            self.assertEqual(response.status_code,400);save.assert_not_called()
            response=client.post('/configuration/settings',data={'provider':'oxen','replicate_token':'FAKE_TOKEN','storage_repo':'example/private'})
            self.assertEqual(response.status_code,200);self.assertNotIn('FAKE_TOKEN',response.text)
            self.assertIn(('REPLICATE_API_TOKEN','FAKE_TOKEN'),[call.args for call in save.call_args_list])

    def test_settings_cannot_switch_during_active_hd(self):
        with patch('config.save_setting') as save,patch.object(app,'jobs',{}),patch.object(app,'hd_jobs',{'a':{'state':'running'}}):
            response=TestClient(app.app).post('/configuration/settings',data={'provider':'replicate'})
            self.assertEqual(response.status_code,409);save.assert_not_called()

    def test_library_does_not_serialize_private_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            runs=Path(directory);folder=runs/('a'*32);folder.mkdir()
            (folder/'status.json').write_text(json.dumps({'state':'error','status':'secret signed URL','key':'SECRET'}))
            with patch.object(app,'RUNS',runs),patch.object(app,'jobs',{}):
                response=TestClient(app.app).get('/library')
                self.assertEqual(response.json()['jobs'][0]['id'],'a'*32)
                self.assertNotIn('SECRET',response.text);self.assertNotIn('signed URL',response.text)

    def test_release_excludes_live_credentials_and_media(self):
        spec=importlib.util.spec_from_file_location('package_release',Path(__file__).resolve().parents[1]/'scripts/package_release.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'static').mkdir();(root/'runs').mkdir()
            (root/'LICENSE').write_text('license');(root/'.env.example').write_text('OXEN_API_KEY=')
            (root/'.env').write_text('SECRET');(root/'.runtime-oxen-job.json').write_text('SECRET')
            (root/'runs/private.mp4').write_bytes(b'PRIVATE');(root/'static/index.html').write_text('<html></html>')
            archive=root/'release.zip';module.package(archive,root)
            with zipfile.ZipFile(archive) as zipped:
                self.assertEqual(set(zipped.namelist()),{'Open-Genjutsu/LICENSE','Open-Genjutsu/.env.example','Open-Genjutsu/static/index.html'})

    def test_reference_library_only_returns_character_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            runs=Path(directory);folder=runs/('a'*32);folder.mkdir()
            (folder/'sirio-reference.jpg').write_bytes(b'photo')
            (folder/'tein-reference.mp4').write_bytes(b'unsupported second identity video')
            (folder/'generation.json').write_text('SECRET')
            (folder/'original.mp4').write_bytes(b'PRIVATE_SOURCE')
            other=runs/'not-a-job';other.mkdir();(other/'sirio-reference.jpg').write_bytes(b'PRIVATE')
            with patch.object(app,'RUNS',runs):
                response=TestClient(app.app).get('/references')
                self.assertEqual(response.status_code,200)
                items=response.json()['references'];self.assertEqual(len(items),1)
                self.assertEqual(items[0]['url'],'/runs/'+folder.name+'/sirio-reference.jpg')
                self.assertNotIn('SECRET',response.text);self.assertNotIn('original.mp4',response.text)

    def test_release_preserves_png_bytes_and_unix_script_format(self):
        spec=importlib.util.spec_from_file_location('package_release',Path(__file__).resolve().parents[1]/'scripts/package_release.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'static').mkdir()
            image=b'\x89PNG\r\n\x1a\nBINARY';(root/'static/og-logo.png').write_bytes(image)
            (root/'setup.sh').write_bytes(b'#!/bin/bash\r\necho ready\r\n')
            archive=root/'release.zip';module.package(archive,root)
            with zipfile.ZipFile(archive) as zipped:
                self.assertEqual(zipped.read('Open-Genjutsu/static/og-logo.png'),image)
                self.assertNotIn(b'\r',zipped.read('Open-Genjutsu/setup.sh'))
                self.assertTrue(zipped.getinfo('Open-Genjutsu/setup.sh').external_attr>>16 & 0o111)

if __name__=='__main__':unittest.main()
