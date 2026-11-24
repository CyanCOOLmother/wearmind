"""Edge profile: image validation only; no cloud image calls."""
import base64

def image_data(value):
    if not isinstance(value, str) or ',' not in value:
        raise ValueError('请选择 JPG、PNG 或 WebP 图片')
    header, encoded = value.split(',', 1)
    if header not in ('data:image/jpeg;base64', 'data:image/png;base64', 'data:image/webp;base64'):
        raise ValueError('仅支持 JPG、PNG 或 WebP')
    raw = base64.b64decode(encoded, validate=True)
    if not 0 < len(raw) <= 3 * 1024 * 1024:
        raise ValueError('图片须小于 3 MB')
    valid = (header.startswith('data:image/jpeg') and raw.startswith(b'\xff\xd8\xff')) or (header.startswith('data:image/png') and raw.startswith(b'\x89PNG\r\n\x1a\n')) or (header.startswith('data:image/webp') and raw[:4] == b'RIFF' and raw[8:12] == b'WEBP')
    if not valid: raise ValueError('图片内容与文件格式不符')
    return value



def status():
    return {'configured':False,'provider':'本地视觉模型尚未接入','model':'未配置','cloud_disabled':True}


def configure(body):
    raise ValueError('开发板本地版禁用云端识别，可先上传照片并手动确认衣物')


def recognize(value,consent):
    raise ValueError('本地视觉模型尚未接入；开发板版不会把照片发送给云端')
