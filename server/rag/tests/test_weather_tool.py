import importlib.util
import json
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / 'weather_tool.py'


class Response:
    def __init__(self, body):
        self.body = json.dumps(body).encode('utf-8')

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        return self.body

    def info(self):
        return {}


class Completions:
    def create(self, **kwargs):
        self.request = kwargs
        return types.SimpleNamespace(choices=[types.SimpleNamespace(
            message=types.SimpleNamespace(content='谨慎飞行'),
        )])


class Client:
    last_instance = None

    def __init__(self, api_key, base_url):
        Client.last_instance = self
        self.api_key = api_key
        self.base_url = base_url
        self.chat = types.SimpleNamespace(completions=Completions())


class WeatherToolTests(unittest.TestCase):
    def setUp(self):
        self.settings = types.SimpleNamespace(
            HEFENG_API_KEY='weather-key',
            HEFENG_API_HOST='https://weather.example.qweatherapi.com',
            DASHSCOPE_API_KEY='qwen-key',
            DASHSCOPE_MODEL='qwen-plus',
            DASHSCOPE_BASE_URL='https://ap-southeast-1.maas.qwencloudapi.com/compatible-mode/v1',
        )
        django = types.ModuleType('django')
        conf = types.ModuleType('django.conf')
        conf.settings = self.settings
        django.conf = conf
        openai = types.ModuleType('openai')
        openai.OpenAI = Client
        dashscope = types.ModuleType('dashscope')
        dashscope.Generation = types.SimpleNamespace(call=lambda **kwargs: None)
        with patch.dict(sys.modules, {
            'django': django, 'django.conf': conf, 'openai': openai, 'dashscope': dashscope,
        }), patch.dict(os.environ, {
            'HEFENG_API_KEY': 'weather-key', 'HEFENG_API_HOST': 'https://weather.example.qweatherapi.com',
            'DASHSCOPE_API_KEY': 'qwen-key',
        }):
            spec = importlib.util.spec_from_file_location('weather_under_test', MODULE_PATH)
            self.module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.module)

    def test_weather_request_uses_private_host_and_key_header(self):
        requests = []
        geo = {'code': '200', 'location': [{
            'name': '北京', 'adm1': '北京市', 'lat': '39.92', 'lon': '116.41', 'id': '101010100',
        }]}
        current = {
            'validTime': '2026-11-15T12:00+08:00',
            'condition': {'text': '多云'},
            'temperature': {'value': 18, 'unit': '°C'},
            'feelsLike': {'value': 17, 'unit': '°C'},
            'humidity': 0.68,
            'wind': {'direction': {'compass': 'nw'}, 'speed': {'value': 4.5, 'unit': 'm/s'}, 'scale': 3},
            'windGust': {'value': 7.2, 'unit': 'm/s'},
            'precipitation': {'amount': {'value': 0, 'unit': 'mm'}, 'type': 'none'},
            'visibility': {'value': 12000, 'unit': 'm'},
        }

        def open_request(request, **kwargs):
            requests.append((request, kwargs))
            return Response(geo if '/geo/v2/city/lookup' in request.full_url else current)

        with patch.object(self.module.urllib.request, 'urlopen', side_effect=open_request):
            result = self.module.get_weather('北京')

        self.assertEqual(len(requests), 2)
        self.assertIn('/weather/v1/current/39.92/116.41', requests[1][0].full_url)
        for request, kwargs in requests:
            self.assertEqual(request.get_header('X-qw-api-key'), 'weather-key')
            self.assertNotIn('key=', request.full_url)
            self.assertNotIn('context', kwargs)
        self.assertEqual(result['wind_speed'], 4.5)
        self.assertEqual(result['vis'], 12)
        self.assertEqual(result['humidity'], 68)

    def test_forecast_uses_v1_daily_and_reads_rain_probability(self):
        self.module._geo_lookup = lambda location: ('39.92', '116.41', '北京', '北京市')
        day = {
            'temperatureMax': {'value': 19}, 'temperatureMin': {'value': 8},
            'daytime': {
                'forecastStartTime': '2026-11-16T07:00+08:00',
                'condition': {'text': '小雨'}, 'humidity': 0.7,
                'wind': {'speed': {'value': 5.5}, 'scale': 4},
                'windGustMax': {'value': 9},
                'precipitation': {'amount': {'value': 2}, 'probability': 0.8, 'type': 'rain'},
            },
            'nighttime': {'condition': {'text': '阴'}},
        }
        urls = []

        def read(url, label):
            urls.append(url)
            return {'days': [day]}

        with patch.object(self.module, '_open_json', side_effect=read):
            result = self.module.get_weather_forecast('北京')
        self.assertIn('/weather/v1/daily/39.92/116.41', urls[0])
        self.assertEqual(result['forecast'][0]['precip_probability'], 80)
        self.assertEqual(result['forecast'][0]['wind_speed_day'], 5.5)

    def test_missing_api_host_is_reported_before_request(self):
        self.settings.HEFENG_API_HOST = ''
        with patch.dict(os.environ, {'HEFENG_API_HOST': ''}):
            with self.assertRaisesRegex(RuntimeError, 'HEFENG_API_HOST'):
                self.module.get_weather('北京')

    def test_extracts_city_without_time_words(self):
        cases = {
            '今天北京适合飞无人机吗？': '北京',
            '上海明天风速多大，能飞穿越机吗？': '上海',
            '深圳今天下午的天气如何？': '深圳',
            '成都这周末适合航拍吗？': '成都',
            '浑南区今天的GPS信号会受磁场干扰吗？': '浑南区',
        }
        for question, city in cases.items():
            with self.subTest(question=question):
                self.assertEqual(self.module._extract_location(question), city)

    def test_weather_answer_uses_configured_qwen_endpoint(self):
        self.module.get_weather = lambda location: {
            'city': '北京市 北京', 'text': '晴', 'temp': 20, 'feels_like': 20,
            'wind_dir': '北风', 'wind_scale': 2, 'wind_speed': 3,
            'wind_gust': 5, 'humidity': 50, 'vis': 10,
            'precip': 0, 'precip_type': 'none', 'obs_time': '2026-11-15T12:00+08:00',
        }
        with patch.dict(sys.modules, {'openai': types.SimpleNamespace(OpenAI=Client)}):
            answer = self.module.weather_agent('今天北京适合飞无人机吗？')
        self.assertIn('谨慎飞行', answer)
        self.assertIn('和风天气', answer)
        self.assertEqual(Client.last_instance.base_url, self.settings.DASHSCOPE_BASE_URL)
        self.assertEqual(Client.last_instance.chat.completions.request['model'], 'qwen-plus')


if __name__ == '__main__':
    unittest.main()
