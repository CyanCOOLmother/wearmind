import unittest
from pathlib import Path
from unittest.mock import patch

from app import npu_pose


class NPUPoseTests(unittest.TestCase):
    def test_missing_model_is_explicit_and_never_cloud(self):
        with patch.dict('os.environ', {'WEARMIND_NPU_POSE_MODEL': '/definitely/not/a/model.cix'}):
            status = npu_pose.status()
            self.assertFalse(status['configured'])
            self.assertTrue(status['cloud_disabled'])
            with self.assertRaisesRegex(ValueError, '不会改用云端'):
                npu_pose.analyze(Path('/missing.jpg'), Path('/tmp/out.jpg'))

    def test_user_facing_tips_do_not_make_body_claims(self):
        self.assertIn('不推断身材', ' '.join(npu_pose._tips(1)))
        self.assertIn('多个人', ' '.join(npu_pose._tips(2)))
