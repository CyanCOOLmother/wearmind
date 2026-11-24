import unittest
from unittest.mock import patch
from app import local_model as lm
from app.engine import recommend

class LocalModelTests(unittest.TestCase):
    def setUp(self): self.original=(lm.RUNTIME,lm.MODEL)
    def tearDown(self): lm.RUNTIME,lm.MODEL=self.original
    def test_loopback_only(self):
        with patch.dict('os.environ',{'WEARMIND_OLLAMA_URL':'https://api.example.com'}):
            with self.assertRaises(ValueError): lm.base_url('ollama')
        with patch.dict('os.environ',{'WEARMIND_OLLAMA_URL':'http://127.0.0.1:11434/path'}):
            with self.assertRaises(ValueError): lm.base_url('ollama')
    def test_filters_cloud_models(self):
        with patch.object(lm,'request_json',return_value={'models':[{'name':'local:3b'},{'name':'model:cloud'},{'name':'remote','remote_host':'https://elsewhere'}]}):
            self.assertEqual(lm.status('ollama')['models'],['local:3b'])
    def test_unavailable_is_explicit(self):
        with patch.object(lm,'request_json',side_effect=OSError()): self.assertFalse(lm.status()['available'])
    def test_config_only_existing(self):
        with patch.object(lm,'status',return_value={'models':['local:3b']}):
            with self.assertRaises(ValueError): lm.configure('ollama','missing')
            self.assertEqual(lm.configure('ollama','local:3b')['model'],'local:3b')
    def test_no_model_no_inference(self):
        lm.MODEL=''
        with patch.object(lm,'request_json') as call:
            with self.assertRaises(ValueError): lm.understand('今天很累')
            call.assert_not_called()
    def test_evidence_validation(self):
        result=lm.validate_result({'feelings':[{'label':'疲惫','evidence':'很累'},{'label':'腰腹敏感','evidence':'虚构的症状'},{'label':'疾病','evidence':'很累'}],'preferred_colors':['蓝色','unknown']},'我很累')
        self.assertEqual(result['feelings'],[{'label':'疲惫','evidence':'很累'}]);self.assertEqual(result['preferred_colors'],['蓝色'])
    def test_mock_local_understanding(self):
        lm.RUNTIME,lm.MODEL='ollama','local:3b'
        with patch.object(lm,'status',return_value={'models':['local:3b']}),patch.object(lm,'request_json',return_value={'message':{'content':'{"feelings":[{"label":"疲惫","evidence":"累"}],"scene":"通勤","preferred_colors":[]}'}}) as call:
            r=lm.understand('今天累，要通勤');self.assertTrue(r['requires_confirmation']);self.assertEqual(r['feelings'][0]['label'],'疲惫');self.assertEqual(call.call_args[0][1],'/api/chat')
    def test_user_flags_control_clothing(self):
        items=[{'id':'tight','name':'裤子','category':'下装','tags':['紧腰'],'color':'#000000'}]
        self.assertIn('下装',recommend({'comfort_flags':['腰腹敏感']},items)['missing'])
        self.assertEqual(len(recommend({'state':'腰不舒服','comfort_flags':[]},items)['outfit']),1)

if __name__=='__main__': unittest.main()
