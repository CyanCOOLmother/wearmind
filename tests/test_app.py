import tempfile
import unittest
import threading
import urllib.request
import urllib.error
import json
from app.engine import recommend
from app import main

class Rules(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); main.DATA=__import__('pathlib').Path(self.tmp.name);main.seed();self.items=main.records('wardrobe')
    def tearDown(self): self.tmp.cleanup()
    def test_sensitive_and_tired(self):
        r=recommend({'state':'疲惫，腰腹敏感'},self.items)
        self.assertFalse(any('紧腰' in x['tags'] or '高跟' in x['tags'] for x in r['outfit']))
        self.assertEqual(len(r['outfit']),3)
    def test_cold_layer(self): self.assertEqual(recommend({'temperature':10},self.items)['outfit'][-1]['category'],'外套')
    def test_rain_shoes(self): self.assertIn('防水',recommend({'weather':'雨天'},self.items)['outfit'][2]['tags'])
    def test_avoid_and_missing(self):
        avoid=[x['id'] for x in self.items if x['category']=='鞋履']
        self.assertIn('鞋履',recommend({},self.items,avoid)['missing'])
    def test_empty(self): self.assertEqual(len(recommend({},[])['missing']),3)
    def test_invalid(self):
        for t in [float('nan'),99]:
            with self.assertRaises(ValueError): recommend({'temperature':t},self.items)
    def test_scene(self): self.assertEqual(recommend({'scene':'运动'},self.items)['outfit'][0]['name'],'白色运动 T 恤')
    def test_persistence(self):
        main.seed(); self.assertEqual(len(main.records('wardrobe')),10)
        main.save('feedback',{'id':'x','action':'avoid','item_id':self.items[0]['id']})
        self.assertEqual(main.records('feedback')[0]['id'],'x')
    def test_http(self):
        server=main.ThreadingHTTPServer(('127.0.0.1',0),main.Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        base='http://127.0.0.1:'+str(server.server_port)
        def post(path,body):
            request=urllib.request.Request(base+path,data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
            return json.load(urllib.request.urlopen(request))
        try:
            self.assertEqual(urllib.request.urlopen(base).status,200)
            saved_body=post('/api/body-state',{'date':'2026-10-14','text':'今天有点累','comfort_flags':['疲惫']})
            self.assertEqual(saved_body['comfort_flags'],['疲惫'])
            stored=json.load(urllib.request.urlopen(base+'/api/body-state'))
            self.assertEqual(stored[0]['text'],'今天有点累')
            device=json.load(urllib.request.urlopen(base+'/api/device'))
            self.assertTrue(device['cloud_disabled'])
            with self.assertRaises(urllib.error.HTTPError): post('/api/vision/config',{'key':'test-only'})
            self.assertEqual(urllib.request.urlopen(base+'/ootd.js').status,200)
            guide=post('/api/ootd',{'environment':'户外步行','weather':'雨天'})
            self.assertEqual(guide['recommended'],'lean')
            asset=next(iter(main.PHOTO_MANIFEST.values()))['file']
            with urllib.request.urlopen(base+'/assets/'+asset) as response:
                self.assertTrue(response.headers['Content-Type'].startswith('image/'))
                response.read()
            with self.assertRaises(urllib.error.HTTPError): urllib.request.urlopen(base+'/assets/../main.py')
            item=post('/api/wardrobe',{'name':'测试衬衫','category':'上装','tags':['舒适']})
            self.assertTrue(item['id'])
            import base64
            photo='data:image/png;base64,'+base64.b64encode(b'\x89PNG\r\n\x1a\n'+b'x'*20).decode()
            photo_item=post('/api/wardrobe',{'name':'照片衣物','category':'上装','tags':[],'photo':photo})
            self.assertEqual(photo_item['photo'],photo)
            status=json.load(urllib.request.urlopen(base+'/api/vision/status'))
            self.assertNotIn('key',status)
            with self.assertRaises(urllib.error.HTTPError): post('/api/vision/recognize',{'image':photo,'consent':False})
            outfit=post('/api/recommend',{'temperature':15})
            self.assertEqual(len(outfit['outfit']),4)
            saved=post('/api/history',{'temperature':15})
            self.assertTrue(saved['id'])
            post('/api/feedback',{'action':'avoid','item_id':outfit['outfit'][0]['id']})
            self.assertNotIn(outfit['outfit'][0]['id'],[i['id'] for i in post('/api/recommend',{'temperature':15})['outfit']])
            with self.assertRaises(urllib.error.HTTPError): post('/api/recommend',{'temperature':100})
        finally: server.shutdown();server.server_close();thread.join()

if __name__=='__main__': unittest.main()
