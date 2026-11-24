import base64
import json
import unittest
from unittest.mock import patch
from app import weather, vision

class WeatherTests(unittest.TestCase):
    def fixture(self):
        return {'timezone':'Asia/Shanghai','current':{'time':'2026-10-14T15:00','temperature_2m':22.5,'apparent_temperature':23,'weather_code':61},'daily':{'time':['2026-10-14','2026-10-15'],'weather_code':[61,71],'temperature_2m_min':[17,2],'temperature_2m_max':[25,9],'precipitation_probability_max':[80,90]}}
    def test_today(self):
        with patch.object(weather,'fetch_json',return_value=self.fixture()) as call:
            r=weather.weather(31.234567,121.474567)
            self.assertEqual(r['weather'],'雨天');self.assertEqual(r['temperature'],22.5)
            self.assertIn('latitude=31.23',call.call_args[0][0])
    def test_future(self):
        with patch.object(weather,'fetch_json',return_value=self.fixture()):
            r=weather.weather(31,121,'2026-10-15');self.assertEqual(r['temperature'],5.5);self.assertEqual(r['weather'],'雪天')
            with self.assertRaises(ValueError): weather.weather(31,121,'2027-01-01')
    def test_bad_coordinates(self):
        for lat in [float('nan'),91,float('inf')]:
            with self.assertRaises(ValueError): weather.weather(lat,121)
    def test_search(self):
        with patch.object(weather,'fetch_json',return_value={'results':[{'name':'上海','latitude':31.23,'longitude':121.47,'country':'中国'}]}):
            self.assertEqual(weather.search_cities('上海')[0]['name'],'上海')

class VisionTests(unittest.TestCase):
    def image(self): return 'data:image/png;base64,'+base64.b64encode(b'\x89PNG\r\n\x1a\n'+b'x'*20).decode()
    def test_format_validation(self):
        self.assertEqual(vision.image_data(self.image()),self.image())
        with self.assertRaises(ValueError): vision.image_data('data:image/png;base64,AAAA')
    def test_cloud_disabled(self):
        self.assertTrue(vision.status()['cloud_disabled'])
        with self.assertRaises(ValueError): vision.configure({'key':'test-only'})
        with self.assertRaises(ValueError): vision.recognize(self.image(),True)

if __name__=='__main__': unittest.main()
