import gzip
import json
import os
import re
import ssl
from http import HTTPStatus
import urllib.error
import urllib.request
import urllib.parse
import dashscope
from dashscope import Generation
from django.conf import settings


_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

TOOLS = [
    {
        'type': 'function',
        'function': {
            'name': 'get_weather',
            'description': (
                '查询指定城市当前实时天气，返回温度、体感温度、风速、风向、湿度、能见度、天气描述。'
                '当用户询问某地是否适合飞无人机、天气怎样、风速多大时调用此工具。'
            ),
            'parameters': {
                'type': 'object',
                'properties': {
                    'location': {
                        'type': 'string',
                        'description': '城市名称，支持中文，例如：上海、浑南区、深圳南山区',
                    }
                },
                'required': ['location'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'get_weather_forecast',
            'description': (
                '查询指定城市未来3天逐日天气预报，返回每天的最高最低温度、风速、降水概率、天气描述。'
                '当用户询问明天/后天/本周天气或规划飞行日期时调用此工具。'
            ),
            'parameters': {
                'type': 'object',
                'properties': {
                    'location': {
                        'type': 'string',
                        'description': '城市名称，支持中文',
                    }
                },
                'required': ['location'],
            },
        },
    },
]

DEFAULT_HEFENG_API_HOST = 'https://j66936n7c4.re.qweatherapi.com'


def _hefeng_key():
    return os.getenv('HEFENG_API_KEY') or getattr(settings, 'HEFENG_API_KEY', '')


def _hefeng_api_host():
    return (os.getenv('HEFENG_API_HOST') or getattr(settings, 'HEFENG_API_HOST', '') or DEFAULT_HEFENG_API_HOST).rstrip('/')


def _read(r):
    raw = r.read()
    if r.info().get('Content-Encoding') == 'gzip' or raw[:2] == b'\x1f\x8b':
        raw = gzip.decompress(raw)
    return json.loads(raw)


def _safe_url(url):
    return re.sub(r'key=[^&]+', 'key=***', url)


def _open_json(url, label):
    try:
        with urllib.request.urlopen(url, timeout=8, context=_SSL_CTX) as r:
            return _read(r)
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        if exc.headers.get('Content-Encoding') == 'gzip' or raw[:2] == b'\x1f\x8b':
            raw = gzip.decompress(raw)
        body = raw.decode('utf-8', errors='replace')[:300]
        raise RuntimeError(f'{label}请求失败，HTTP {exc.code}。请检查 HEFENG_API_KEY 和 HEFENG_API_HOST 是否匹配。返回：{body}') from exc


def _geo_lookup(location):
    hefeng_key = _hefeng_key()
    if not hefeng_key:
        raise RuntimeError('缺少 HEFENG_API_KEY，请在 .env 中配置')
    api_host = _hefeng_api_host()
    url = (
        f'{api_host}/geo/v2/city/lookup?'
        + urllib.parse.urlencode({'location': location, 'key': hefeng_key, 'lang': 'zh'})
    )
    print(f'[weather] geo lookup: {_safe_url(url)}')
    data = _open_json(url, '城市查询')
    print(f'[weather] geo response code: {data.get("code")}, locations: {len(data.get("location", []))}')
    if data.get('code') != '200' or not data.get('location'):
        raise RuntimeError(f'城市 "{location}" 未找到（code={data.get("code")}），请输入更准确的地名')
    loc = data['location'][0]
    print(f'[weather] matched: {loc["name"]} / {loc["adm1"]} / id={loc["id"]}')
    return loc['id'], loc['name'], loc['adm1']


def get_weather(location):
    loc_id, city_name, province = _geo_lookup(location)
    hefeng_key = _hefeng_key()
    api_host = _hefeng_api_host()
    url = (
        f'{api_host}/v7/weather/now?'
        + urllib.parse.urlencode({'location': loc_id, 'key': hefeng_key, 'lang': 'zh', 'unit': 'm'})
    )
    print(f'[weather] now url: {_safe_url(url)}')
    data = _open_json(url, '实时天气')
    print(f'[weather] now response code: {data.get("code")}')
    if data.get('code') != '200':
        raise RuntimeError(f'实时天气查询失败，API返回 code={data.get("code")}')
    now = data['now']
    return {
        'city': f'{province} {city_name}',
        'temp': now['temp'],
        'feels_like': now['feelsLike'],
        'text': now['text'],
        'wind_dir': now['windDir'],
        'wind_scale': now['windScale'],
        'wind_speed': now['windSpeed'],
        'humidity': now['humidity'],
        'vis': now['vis'],
        'obs_time': now['obsTime'],
    }


def get_weather_forecast(location):
    loc_id, city_name, province = _geo_lookup(location)
    hefeng_key = _hefeng_key()
    api_host = _hefeng_api_host()
    url = (
        f'{api_host}/v7/weather/3d?'
        + urllib.parse.urlencode({'location': loc_id, 'key': hefeng_key, 'lang': 'zh', 'unit': 'm'})
    )
    print(f'[weather] forecast url: {_safe_url(url)}')
    data = _open_json(url, '天气预报')
    print(f'[weather] forecast response code: {data.get("code")}')
    if data.get('code') != '200':
        raise RuntimeError(f'天气预报查询失败，API返回 code={data.get("code")}')
    days = []
    for d in data['daily']:
        days.append({
            'date': d['fxDate'],
            'text_day': d['textDay'],
            'text_night': d['textNight'],
            'temp_max': d['tempMax'],
            'temp_min': d['tempMin'],
            'wind_dir_day': d['windDirDay'],
            'wind_scale_day': d['windScaleDay'],
            'wind_speed_day': d['windSpeedDay'],
            'humidity': d['humidity'],
            'precip': d['precip'],
            'uv_index': d['uvIndex'],
            'vis': d['vis'],
        })
    return {'city': f'{province} {city_name}', 'forecast': days}


def _call_tool(name, args):
    print(f'[weather] calling tool: {name}, args: {args}')
    if name == 'get_weather':
        return get_weather(args['location'])
    if name == 'get_weather_forecast':
        return get_weather_forecast(args['location'])
    raise RuntimeError(f'未知工具：{name}')


def _extract_location(question):
    patterns = [
        r'(?:今天|明天|后天|现在|当前)?\s*([\u4e00-\u9fa5]{2,10}(?:区|县|市|州|盟|旗|镇|乡)?)\s*(?:今天|明天|后天|现在|当前|上午|下午|晚上|这周末|周末|天气|风速|适合|能|可以|的)',
        r'(?:查询|看看|评估)\s*([\u4e00-\u9fa5]{2,10}(?:区|县|市|州|盟|旗|镇|乡)?)',
    ]
    for pattern in patterns:
        match = re.search(pattern, question)
        if match:
            return match.group(1)
    cleaned = re.sub(
        r'(今天|明天|后天|现在|当前|上午|下午|晚上|这周末|周末|天气|风速|适合|无人机|航拍|穿越机|飞|吗|怎样|如何|多大|[，。！？?])',
        '',
        question,
    ).strip()
    if 2 <= len(cleaned) <= 10:
        return cleaned
    raise RuntimeError('未识别到城市或地区，请在问题中写明地点，例如：今天北京适合飞无人机吗？')


def _needs_forecast(question):
    return any(word in question for word in ['明天', '后天', '未来', '预报', '周末', '本周', '这周'])


def _rule_based_summary(weather_data, forecast=False):
    if forecast:
        lines = [f'查询地点：{weather_data["city"]}']
        for day in weather_data['forecast']:
            lines.append(
                f'{day["date"]}：白天{day["text_day"]}，夜间{day["text_night"]}，'
                f'温度{day["temp_min"]}~{day["temp_max"]}℃，'
                f'风速{day["wind_speed_day"]}km/h，风力{day["wind_scale_day"]}级，'
                f'湿度{day["humidity"]}%，能见度{day["vis"]}km，降水量{day["precip"]}mm。'
            )
        return '\n'.join(lines)
    return (
        f'查询地点：{weather_data["city"]}\n'
        f'天气：{weather_data["text"]}\n'
        f'温度：{weather_data["temp"]}℃，体感温度：{weather_data["feels_like"]}℃\n'
        f'风向：{weather_data["wind_dir"]}，风力：{weather_data["wind_scale"]}级，风速：{weather_data["wind_speed"]}km/h\n'
        f'湿度：{weather_data["humidity"]}%，能见度：{weather_data["vis"]}km\n'
        f'观测时间：{weather_data["obs_time"]}'
    )


def weather_agent(question):
    api_key = os.getenv('DASHSCOPE_API_KEY') or getattr(settings, 'DASHSCOPE_API_KEY', '')
    if not api_key:
        raise RuntimeError('缺少 DASHSCOPE_API_KEY')
    dashscope.api_key = api_key
    chat_model = os.getenv('DASHSCOPE_MODEL') or getattr(settings, 'DASHSCOPE_MODEL', 'qwen-plus')
    print(f'[weather] agent start, model={chat_model}, question={question}')

    location = _extract_location(question)
    forecast = _needs_forecast(question)
    weather_data = get_weather_forecast(location) if forecast else get_weather(location)
    weather_summary = _rule_based_summary(weather_data, forecast=forecast)

    system_prompt = (
        '你是无人机飞行气象顾问。根据天气数据，结合无人机安全飞行标准给出专业建议：'
        '风速 < 5m/s 适合飞行，5~8m/s 需谨慎，> 8m/s 建议停飞；'
        '能见度 < 1km 禁飞；降水、雷暴天气禁飞；湿度 > 90% 注意电子设备防潮。'
        '回答要给出明确的"适合/谨慎/不适合飞行"结论，并说明原因。'
        '如果风速单位是 km/h，请先换算成 m/s 后再判断。'
        '回答结构包含：结论、天气依据、飞行风险、实训操作建议。'
    )

    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': f'用户问题：{question}\n\n和风天气数据：\n{weather_summary}'},
    ]

    resp = Generation.call(
        model=chat_model,
        messages=messages,
        temperature=0.2,
        max_tokens=1200,
        result_format='message',
        enable_thinking=False,
    )
    print(f'[weather] resp status={resp.status_code}')
    if resp.status_code != HTTPStatus.OK:
        raise RuntimeError(f'模型调用失败：{resp.code} {resp.message}')

    choice = resp.output.choices[0]
    content = choice.message.content
    if isinstance(content, list):
        return content[0].get('text', str(content[0]))
    return content
