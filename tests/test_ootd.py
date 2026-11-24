import json
import unittest
from pathlib import Path
from app.ootd import guidance
from app import main

class OOTDTests(unittest.TestCase):
    def test_walking_environment(self): self.assertEqual(guidance({'environment':'户外步行'})['recommended'],'walk')
    def test_tired_prefers_sitting(self): self.assertEqual(guidance({'state':'腰腹不舒服，有点累','environment':'户外步行'})['recommended'],'sit')
    def test_destination_rain_overrides(self):
        g=guidance({'weather':'晴天','destination_weather':{'weather':'雨天'},'environment':'户外步行'})
        self.assertEqual(g['recommended'],'lean');self.assertTrue(any('雨天' in n for n in g['notes']))
    def test_all_poses_have_instructions(self):
        for p in guidance({})['poses']:
            self.assertEqual(len(p['steps']),3)
            self.assertTrue(all(p[k] for k in ('lens','frame','light')))
    def test_active_references_are_alpha_png(self):
        for asset in main.PHOTO_MANIFEST.values():
            raw=(main.ROOT/'static/assets'/asset['file']).read_bytes()
            self.assertEqual(raw[:8],b'\x89PNG\r\n\x1a\n')
            self.assertIn(raw[25],(4,6))
    def test_reference_assets_present(self):
        self.assertEqual(len(main.PHOTO_MANIFEST),10)
        for asset in main.PHOTO_MANIFEST.values():
            self.assertTrue((main.ROOT/'static/assets'/asset['file']).is_file())
            self.assertTrue(asset['source_url'].startswith('https://'))

if __name__=='__main__': unittest.main()
