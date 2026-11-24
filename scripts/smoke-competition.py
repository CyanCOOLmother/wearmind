"""Run real local WearMind demo checks on the CIX board without changing the wardrobe."""
import base64
import json
from pathlib import Path
from urllib.request import Request, urlopen

BASE = 'http://127.0.0.1:8790'
ROOT = Path('/home/cix/wearmind-v2-release-20261108-122821')
SAMPLE = Path('/home/cix/wearmind-npu/cix-demo/models/ComputeVision/Pose_Estimation/onnx_yolov11n_pose/test_data/2.jpeg')


def api(path, body=None, timeout=15):
    request = Request(BASE + path,
                      data=None if body is None else json.dumps(body, ensure_ascii=False).encode(),
                      headers={'Content-Type': 'application/json'})
    with urlopen(request, timeout=timeout) as response:
        return json.load(response)


def main():
    with urlopen(BASE + '/', timeout=10) as response:
        assert '衣伴决赛演示版' in response.read().decode()
    device = api('/api/device')
    assert device['board_verified'] and device['cloud_disabled'], device
    items = api('/api/wardrobe')
    assert items, '衣橱为空'
    model = api('/api/local-model/status?runtime=llamacpp')
    assert model['available'] and model['selected'], model
    understood = api('/api/local-model/understand',
                     {'text': '今天去公司通勤，想穿蓝色，感觉有点怕冷。'}, timeout=120)
    assert understood['requires_confirmation'] and understood['model'], understood
    result = api('/api/recommend', {'scene': '通勤', 'temperature': 18, 'weather': '晴天',
                                   'state': '感觉有点怕冷。', 'comfort_flags': ['怕冷']})
    known = {item['id'] for item in items}
    assert result['outfit'] and all(item['id'] in known for item in result['outfit']), result
    pose = api('/api/npu-pose/status')
    assert pose['configured'], pose
    assert SAMPLE.is_file(), SAMPLE
    encoded = base64.b64encode(SAMPLE.read_bytes()).decode()
    analysis = api('/api/ootd/npu-pose',
                   {'image': 'data:image/jpeg;base64,' + encoded}, timeout=120)
    assert analysis['provider'] == 'CIX NPU / YOLOv11n-Pose', analysis
    assert analysis['people'] >= 1 and analysis['image_url'].startswith('/media/pose/'), analysis
    token = Path(analysis['image_url']).stem
    # Remove only this run's generated official sample image; keep the user's photos intact.
    for path in (ROOT / 'data/pose-uploads' / (token + '.jpg'),
                 ROOT / 'data/pose-media' / (token + '.jpg')):
        path.unlink(missing_ok=True)
    print('PASS: 蓝白首页、开发板识别、衣橱读取、本机 Qwen、真实推荐、CIX NPU 图片推理')
    print('Qwen 耗时: %s ms；NPU 耗时: %s ms；识别人物: %s' %
          (understood['elapsed_ms'], analysis['elapsed_ms'], analysis['people']))


if __name__ == '__main__':
    main()
