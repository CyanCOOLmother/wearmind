"""Repeat read-only board checks and report real latency; does not alter wardrobe."""
import json
import statistics
import time
from urllib.request import Request, urlopen

BASE = 'http://127.0.0.1:8790'


def request(path, body=None, timeout=120):
    payload = None if body is None else json.dumps(body, ensure_ascii=False).encode()
    req = Request(BASE + path, data=payload, headers={'Content-Type': 'application/json'})
    start = time.perf_counter()
    with urlopen(req, timeout=timeout) as response:
        data = json.load(response)
    return data, round((time.perf_counter() - start) * 1000)


def main():
    device, _ = request('/api/device')
    assert device['board_verified'] and device['cloud_disabled'], device
    wardrobe, _ = request('/api/wardrobe')
    assert wardrobe, '衣橱为空'
    measures = {'qwen_ms': [], 'recommend_ms': []}
    for _ in range(3):
        understood, elapsed = request('/api/local-model/understand',
                                      {'text': '今天去公司通勤，有点怕冷。'})
        assert understood['requires_confirmation'] and understood['model'], understood
        measures['qwen_ms'].append(elapsed)
        outfit, elapsed = request('/api/recommend',
                                  {'scene': '通勤', 'temperature': 18, 'weather': '晴天',
                                   'state': '有点怕冷。', 'comfort_flags': ['怕冷']})
        assert outfit['outfit'], outfit
        measures['recommend_ms'].append(elapsed)
    result = {'runs': 3, 'device': device['environment'],
              'qwen_ms': measures['qwen_ms'],
              'qwen_median_ms': round(statistics.median(measures['qwen_ms'])),
              'recommend_ms': measures['recommend_ms'],
              'recommend_median_ms': round(statistics.median(measures['recommend_ms'])),
              'note': 'Qwen 为开发板 CPU 本地推理；推荐为本地规则。NPU 请运行 smoke-competition.py 单独验证。'}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
