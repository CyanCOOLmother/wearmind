"""Run: python3 -m app.main. Loopback-only local development server."""
import json
import base64
import os
import sqlite3
import uuid
import re
import platform
from urllib.parse import urlsplit, parse_qs
from urllib.error import URLError, HTTPError
from . import weather as weather_tool, vision, npu_pose
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from .engine import recommend, CATEGORIES
from .colors import PALETTE
from .ootd import guidance
from . import local_model

ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get('WEARMIND_DATA', ROOT.parent / 'data'))
POSE_MEDIA = DATA / 'pose-media'
PHOTO_MANIFEST = json.loads((ROOT/'static/assets/manifest.json').read_text())

def db():
    DATA.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DATA / 'wearmind.sqlite3')
    c.execute('CREATE TABLE IF NOT EXISTS records (id TEXT PRIMARY KEY, kind TEXT, body TEXT)')
    return c

def records(kind):
    with db() as c: result=[json.loads(r[0]) for r in c.execute('SELECT body FROM records WHERE kind=? ORDER BY rowid', (kind,))]
    if kind == 'wardrobe':
        for item in result:
            asset=PHOTO_MANIFEST.get(item.get('name'))
            if asset and not item.get('photo') and item.get('color') == asset['original_color']:
                item.update(reference_photo='/assets/'+asset['file'],reference_source=asset['source_url'])
    return result

def save(kind, body):
    with db() as c: c.execute('INSERT OR REPLACE INTO records VALUES (?,?,?)', (body['id'], kind, json.dumps(body, ensure_ascii=False)))

def seed():
    with db() as c:
        if c.execute('SELECT 1 FROM records WHERE kind="initialized"').fetchone(): return
    for name,cat,tags,color in [
        ('米白柔软针织衫','上装',['舒适','通勤','保暖'],'#e4d9c4'),
        ('浅蓝棉衬衫','上装',['客户会面','通勤','透气'],'#b8ced2'),
        ('白色运动 T 恤','上装',['运动','休闲','透气','舒适'],'#f0eee8'),
        ('黑色松紧阔腿裤','下装',['舒适','通勤','客户会面'],'#414448'),
        ('灰色运动裤','下装',['舒适','运动','休闲'],'#a1a49e'),
        ('修身牛仔裤','下装',['紧腰','休闲'],'#65778c'),
        ('小白鞋','鞋履',['舒适','通勤','运动','怕水'],'#ece9df'),
        ('防水平底短靴','鞋履',['防水','客户会面','舒适'],'#8a6955'),
        ('轻暖开衫','外套',['保暖','舒适','通勤'],'#b7a08a'),
        ('羊毛大衣','外套',['保暖','厚重','客户会面'],'#766456')]:
        save('wardrobe',dict(id=uuid.uuid4().hex,name=name,category=cat,tags=tags,color=color))
    save('initialized',{'id':'seed-v1'})

class Handler(BaseHTTPRequestHandler):
    def output(self, code, data):
        raw = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        parsed=urlsplit(self.path)
        query={k:v[0] for k,v in parse_qs(parsed.query).items()}
        try:
            if parsed.path == '/api/cities': return self.output(200,weather_tool.search_cities(query.get('q','')))
            if parsed.path == '/api/weather': return self.output(200,weather_tool.weather(query.get('lat'),query.get('lon'),query.get('date')))
            if parsed.path == '/api/local-model/status': return self.output(200,local_model.status(query.get('runtime')))
            if parsed.path == '/api/body-state': return self.output(200,records('body-state'))
            if parsed.path == '/api/device':
                is_board = platform.machine() in ('aarch64', 'arm64') and Path('/usr/share/cix/bin/llama-server').is_file()
                return self.output(200,{'profile':'开发板本地模型版','storage':'数据保存在运行此服务的设备本地','cloud_disabled':True,'board_verified':is_board,'environment':'CIX 开发板本机运行' if is_board else ('Mac 验证环境' if platform.system()=='Darwin' else '当前运行设备')})
            if parsed.path == '/api/vision/status': return self.output(200,vision.status())
            if parsed.path == '/api/npu-pose/status': return self.output(200,npu_pose.status())
        except (ValueError,TypeError,KeyError): return self.output(400,{'error':'城市、坐标或日期无效，或日期超出可用预报范围'})
        except (URLError,TimeoutError,OSError): return self.output(502,{'error':'天气服务暂时不可用，请稍后重试或手动填写；不会用示例天气替代'})
        if self.path in ('/api/wardrobe','/api/history','/api/feedback'):
            return self.output(200, records(self.path.split('/')[-1]))
        if parsed.path.startswith('/assets/'):
            name=parsed.path.removeprefix('/assets/')
            allowed={asset[key] for asset in PHOTO_MANIFEST.values() for key in ('file','original_file') if key in asset}
            if name not in allowed: return self.output(404,{'error':'图片不存在'})
            asset=ROOT/'static/assets'/name
            if not asset.is_file(): return self.output(404,{'error':'图片不存在'})
            import mimetypes
            raw=asset.read_bytes();self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(name)[0] or 'application/octet-stream');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw);return
        if parsed.path.startswith('/media/pose/'):
            name=Path(parsed.path).name
            asset=POSE_MEDIA/name
            if not name.endswith('.jpg') or not asset.is_file(): return self.output(404,{'error':'分析图片不存在'})
            raw=asset.read_bytes();self.send_response(200);self.send_header('Content-Type','image/jpeg');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw);return
        names={'/':'classic.html','/classic':'classic.html','/simple':'home.html','/style.css':'style.css','/app.js':'app.js','/ootd.js':'ootd.js','/edge.js':'edge.js','/demo.js':'demo.js','/wardrobe-flow.js':'wardrobe-flow.js','/focus-flow.js':'focus-flow.js'}
        if self.path not in names: return self.output(404,{'error':'页面不存在'})
        p=ROOT/'static'/names[self.path]
        raw=p.read_bytes()
        if self.path == '/simple': raw=raw.replace(b'</html>',b'<script src="/demo.js"></script><script src="/wardrobe-flow.js"></script><script src="/focus-flow.js"></script></html>')
        # The board serves a single local UI during development and demos.  Never
        # let the browser silently reuse an older page after an on-device update.
        self.send_response(200); self.send_header('Content-Type',{'html':'text/html; charset=utf-8','css':'text/css','js':'text/javascript'}[p.suffix[1:]]); self.send_header('Cache-Control','no-store, max-age=0'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def do_POST(self):
        # Only same-origin browser requests may mutate local personal data.
        if self.headers.get('Origin') not in (None, 'http://' + self.headers.get('Host','')):
            return self.output(403,{'error':'不允许跨站请求'})
        try:
            size=int(self.headers.get('Content-Length',0))
            if not 0 < size <= 4500000: raise ValueError('请求大小无效')
            body=json.loads(self.rfile.read(size))
            if not isinstance(body,dict): raise ValueError('数据格式无效')
            if self.path == '/api/local-model/config':
                result=local_model.configure(body.get('runtime'),body.get('model'))
                save('model-settings',{'id':'active',**result})
            elif self.path == '/api/local-model/understand':
                result=local_model.understand(body.get('text'))
            elif self.path == '/api/body-state':
                from datetime import date,datetime,timezone
                text=body.get('text','')
                if not isinstance(text,str) or not 1<=len(text.strip())<=500: raise ValueError('请填写今天的感受（最多 500 字）')
                day=date.fromisoformat(body.get('date','')).isoformat()
                flags=body.get('comfort_flags')
                if flags is not None and (not isinstance(flags,list) or any(x not in local_model.FLAGS for x in flags)): raise ValueError('感受标签无效')
                result={'id':'body-'+day,'date':day,'text':text,'comfort_flags':flags,'saved_at':datetime.now(timezone.utc).isoformat()}
                save('body-state',result)
            elif self.path == '/api/vision/config':
                result=vision.configure(body)
            elif self.path == '/api/vision/recognize':
                result=vision.recognize(body.get('image'),body.get('consent'))
            elif self.path == '/api/ootd':
                result=guidance(body)
            elif self.path == '/api/ootd/npu-pose':
                value=vision.image_data(body.get('image'))
                header, encoded=value.split(',',1)
                raw=base64.b64decode(encoded,validate=True)
                suffix={'data:image/jpeg;base64':'.jpg','data:image/png;base64':'.png','data:image/webp;base64':'.webp'}[header]
                token=uuid.uuid4().hex
                upload_dir=DATA/'pose-uploads'; upload_dir.mkdir(parents=True,exist_ok=True)
                source=upload_dir/(token+suffix)
                source.write_bytes(raw)
                result=npu_pose.analyze(source,POSE_MEDIA/(token+'.jpg'))
                result.update(image_url='/media/pose/'+token+'.jpg',source='照片仅在开发板本机处理；未发送到云端')
            elif self.path == '/api/recommend':
                avoided=[x['item_id'] for x in records('feedback') if x.get('action')=='avoid']
                result=recommend(body,records('wardrobe'),avoided)
            elif self.path == '/api/wardrobe':
                name=str(body.get('name','')).strip()[:60]
                if not name or body.get('category') not in CATEGORIES: raise ValueError('请填写衣物名称与分类')
                tags=body.get('tags',[])
                allowed={'舒适','紧腰','高跟','防水','怕水','保暖','透气','厚重','通勤','客户会面','休闲','运动','约会','遮手臂','不卡腰','好活动','耐脏','抗皱','空调房','显高','温柔风','中性风','成熟风'}
                if not isinstance(tags,list) or any(t not in allowed for t in tags): raise ValueError('衣物标签无效')
                photo=body.get('photo')
                if photo: photo=vision.image_data(photo)
                color=body.get('color','#c5b5a4')
                if not isinstance(color,str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',color): color='#c5b5a4'
                color_name=body.get('color_name')
                if color_name is not None and color_name not in PALETTE: raise ValueError('请选择有效的衣物颜色')
                if color_name: color=PALETTE[color_name]
                result=dict(id=uuid.uuid4().hex,name=name,category=body['category'],tags=tags,color=color)
                if color_name: result['color_name']=color_name
                if photo: result['photo']=photo
                save('wardrobe',result)
            elif self.path == '/api/history':
                result=recommend(body,records('wardrobe'),[x['item_id'] for x in records('feedback') if x.get('action')=='avoid'])
                from datetime import datetime
                result.update(id=uuid.uuid4().hex,created_at=datetime.now().astimezone().isoformat()); save('history',result)
            elif self.path == '/api/feedback':
                if body.get('action') not in ('accept','avoid'): raise ValueError('反馈类型无效')
                if body['action']=='avoid' and body.get('item_id') not in [i['id'] for i in records('wardrobe')]: raise ValueError('单品不存在')
                result=dict(id=uuid.uuid4().hex,action=body['action'],item_id=body.get('item_id'),reason=str(body.get('reason',''))[:300]); save('feedback',result)
            else: return self.output(404,{'error':'接口不存在'})
            self.output(200,result)
        except (ValueError, TypeError, KeyError) as error:
            self.output(400,{'error':str(error) if isinstance(error,ValueError) else '输入无效，请检查填写信息'})
        except HTTPError as error:
            self.output(502,{'error': '本机模型服务拒绝请求，请检查模型运行状态（HTTP '+str(error.code)+'）'})
        except (URLError,TimeoutError,OSError):
            self.output(502,{'error':'本机模型连接失败或超时；可以手动填写，不会改用云端'})
    def log_message(self, *args): pass

if __name__=='__main__':
    seed()
    saved_settings=records('model-settings')
    if saved_settings:
        config=saved_settings[-1]
        local_model.RUNTIME=config.get('runtime','ollama')
        local_model.MODEL=config.get('model','')
    port=int(os.environ.get('WEARMIND_PORT','8765'))
    # A previous preview may still be running; start separately without stopping it.
    strict_port = os.environ.get('WEARMIND_STRICT_PORT') == '1'
    for candidate in range(port,port+(1 if strict_port else 10)):
        try:
            server=ThreadingHTTPServer(('127.0.0.1',candidate),Handler)
            port=candidate
            break
        except OSError as error:
            import errno
            if error.errno != errno.EADDRINUSE: raise
    else:
        raise SystemExit('本地预览端口已占用，请先关闭旧的衣伴启动窗口再试。')
    if os.environ.get('WEARMIND_OPEN_BROWSER') == '1':
        import webbrowser
        webbrowser.open(f'http://127.0.0.1:{port}')
    print(f'衣伴已启动：http://127.0.0.1:{port}',flush=True)
    server.serve_forever()
