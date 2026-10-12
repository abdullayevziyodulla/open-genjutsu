import unittest,tempfile,json
from pathlib import Path
from unittest.mock import patch,Mock
import mask_review,seedance_bridge

class WorkflowTests(unittest.TestCase):
 def test_mask_changed_invalidates_approval(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)
   for name in mask_review.FILES:(p/name).write_bytes(b'original')
   fingerprint=mask_review.fingerprint(p)
   mask_review.review(p,True,'Entire clip reviewed',fingerprint)
   mask_review.require_approved(p)
   (p/'mask.mp4').write_bytes(b'changed')
   with self.assertRaises(ValueError):mask_review.require_approved(p)
   with self.assertRaises(ValueError):mask_review.review(p,True,'stale',fingerprint)
 def test_provider_selection_dispatches_once_without_network(self):
  for provider,module in [('oxen','oxen_seedance'),('lec','lec_seedance'),('replicate','replicate_seedance')]:
   with patch('seedance_bridge.setting',return_value=provider),patch(module+'.submit',return_value='saved-id') as submit:
    self.assertEqual(seedance_bridge.submit('folder','prompt','photo'),'saved-id')
    submit.assert_called_once_with('folder','prompt','photo',None,print)
 def test_unknown_provider_cannot_fall_back_to_paid_service(self):
  with patch('seedance_bridge.setting',return_value='unsupported'),patch('oxen_seedance.requests.post') as post:
   with self.assertRaises(ValueError):seedance_bridge.submit('folder','prompt','photo')
   post.assert_not_called()
 def test_existing_submission_not_requeued(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'seedance-response.json').write_text('{}')
   with patch('seedance_bridge.setting',return_value='replicate'),patch('replicate_seedance.require_approved'),patch('replicate_seedance.requests.post') as post:
    with self.assertRaises(ValueError):seedance_bridge.submit(p,'prompt','reference.png')
    post.assert_not_called()
 def test_collection_uses_saved_provider_not_current_settings(self):
  with patch('replicate_seedance.saved_provider',return_value='oxen'),patch('seedance_bridge.setting',return_value='lec'),patch('oxen_seedance.wait_and_finish') as collect,patch('lec_seedance.wait_and_finish') as wrong:
   seedance_bridge.wait_and_finish('folder','saved-id');collect.assert_called_once_with('folder','saved-id',print);wrong.assert_not_called()
 def test_hd_uses_saved_provider(self):
  with patch('replicate_seedance.saved_provider',return_value='oxen'),patch('oxen_seedance.submit_hd',return_value='hd-id') as hd:
   self.assertEqual(seedance_bridge.submit_hd('folder'),'hd-id');hd.assert_called_once_with('folder')

if __name__=='__main__':unittest.main()
