"""Open-Meteo city lookup and weather. User-triggered; no background location."""
import json
import math
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import urlopen, Request


def fetch_json(url):
    with urlopen(Request(url, headers={'User-Agent': 'WearMind-local/0.2'}), timeout=15) as response:
        return json.load(response)


def search_cities(query):
    query = str(query).strip()
    if not 2 <= len(query) <= 80:
        raise ValueError('请输入至少两个字的城市名')
    data = fetch_json('https://geocoding-api.open-meteo.com/v1/search?' + urlencode(
        {'name': query, 'count': 8, 'language': 'zh', 'format': 'json'}))
    return [{'name': x['name'], 'region': x.get('admin1', ''), 'country': x.get('country', ''),
             'latitude': x['latitude'], 'longitude': x['longitude']} for x in data.get('results', [])]


def weather(latitude, longitude, day=None):
    lat, lon = float(latitude), float(longitude)
    if not math.isfinite(lat) or not math.isfinite(lon) or not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError('定位坐标无效')
    # Round to roughly city/neighbourhood scale before transmitting to weather provider.
    lat, lon = round(lat, 2), round(lon, 2)
    params = dict(latitude=lat, longitude=lon, timezone='auto', forecast_days=16,
                  current='temperature_2m,apparent_temperature,weather_code',
                  daily='weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max')
    data = fetch_json('https://api.open-meteo.com/v1/forecast?' + urlencode(params))
    daily = data['daily']
    target = day or data['current']['time'][:10]
    if target not in daily['time']:
        raise ValueError('该日期暂不在可用预报范围内，请在临近出发时再查询')
    i = daily['time'].index(target)
    now = data['current']
    is_today = target == now['time'][:10]
    code = int(now['weather_code'] if is_today else daily['weather_code'][i])
    kind = '雨天' if code in (51,53,55,56,57,61,63,65,66,67,80,81,82,95,96,99) else ('雪天' if code in (71,73,75,77,85,86) else ('晴天' if code <= 1 else '阴天'))
    lo, hi = daily['temperature_2m_min'][i], daily['temperature_2m_max'][i]
    return dict(date=target, temperature=now['temperature_2m'] if is_today else round((lo+hi)/2,1),
                apparent_temperature=now.get('apparent_temperature') if is_today else None,
                low=lo, high=hi, rain_probability=daily['precipitation_probability_max'][i],
                weather=kind, weather_code=code, timezone=data['timezone'],
                observed_at=now['time'] if is_today else None,
                fetched_at=datetime.now(timezone.utc).isoformat(),
                source='Open-Meteo', source_url='https://open-meteo.com/',
                mode='当前天气与今日预报' if is_today else '目的地当日预报（推荐使用高低温均值）')
