import unittest,tempfile,json
from pathlib import Path
from unittest.mock import patch,Mock
import mask_review,seedance_bridge
class FaceMeshTests(unittest.TestCase):
 def test_mesh_approval_tracks_overlay_and_audio_without_masks(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'workflow-mode.json').write_text('{"mode":"face_mesh"}')
   for n in ['original.mp4','face-landmarks.json','composite-silent.mp4','seedance-input.mp4']:(p/n).write_bytes(b'test')
   mask_review.review(p,True,'Full mesh reviewed',mask_review.fingerprint(p));mask_review.require_approved(p)
   (p/'seedance-input.mp4').write_bytes(b'changed')
   with self.assertRaises(ValueError):mask_review.require_approved(p)
 def test_mesh_submission_does_not_rebuild_depth_input(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'workflow-mode.json').write_text('{"mode":"face_mesh"}');(p/'audio-manifest.json').write_text('{}')
   from replicate_seedance import build_prompt
   prompt=build_prompt(p,'Replace subject')
   self.assertIn('original video with face mesh overlay',prompt)
   self.assertIn('Remove all depth colors and face mesh lines',prompt)
   self.assertNotIn('colored-depth composite',prompt)
