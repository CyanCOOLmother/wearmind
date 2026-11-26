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

    def test_composition_reports_missing_feet_without_clothing_claim(self):
        points=[(50,50,.9) for _ in range(17)]
        points[15]=(-1,101,.1);points[16]=(-1,101,.1)
        result=npu_pose._composition((5,5,95,100),points,100,100)
        self.assertFalse(result['feet_clear'])
        self.assertIn('鞋履',' '.join(result['tips']))
        self.assertNotIn('识别到鞋',' '.join(result['tips']))

    def test_composition_full_body_visible(self):
        points=[(50,50,.9) for _ in range(17)]
        result=npu_pose._composition((10,10,90,90),points,100,100)
        self.assertEqual(result['coverage'],'全身关键点可见')
        self.assertTrue(result['feet_clear'])
