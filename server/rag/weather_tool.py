import gzip
import json
import os
import re
import urllib.error
import urllib.request
import urllib.parse
from openai import OpenAI
from django.conf import settings


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

def _hefeng_key():
    key = os.getenv('HEFENG_API_KEY') or getattr(settings, 'HEFENG_API_KEY', '')
    if not key:
        raise RuntimeError('缺少 HEFENG_API_KEY，请在 server/.env 中配置和风天气凭据')
    return key


def _hefeng_api_host():
    host = (os.getenv('HEFENG_API_HOST') or getattr(settings, 'HEFENG_API_HOST', '')).rstrip('/')
    if not host:
        raise RuntimeError('缺少 HEFENG_API_HOST，请从和风天气控制台的设置页面复制专属 API Host')
    parsed = urllib.parse.urlparse(host)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.path or parsed.query or parsed.fragment:
        raise RuntimeError('HEFENG_API_HOST 必须是 https:// 开头的专属 API Host，不能带路径或参数')
    return host


def _read(r):
    raw = r.read()
    if r.info().get('Content-Encoding') == 'gzip' or raw[:2] == b'\x1f\x8b':
        raw = gzip.decompress(raw)
    return json.loads(raw)


def _open_json(url, label):
    request = urllib.request.Request(url, headers={
        'X-QW-Api-Key': _hefeng_key(),
        'Accept-Encoding': 'gzip',
    })
    try:
        with urllib.request.urlopen(request, timeout=8) as r:
            return _read(r)
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        if exc.headers.get('Content-Encoding') == 'gzip' or raw[:2] == b'\x1f\x8b':
            raw = gzip.decompress(raw)
        body = raw.decode('utf-8', errors='replace')[:300]
        raise RuntimeError(f'{label}请求失败，HTTP {exc.code}。请检查 HEFENG_API_KEY 和 HEFENG_API_HOST 是否匹配。返回：{body}') from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f'{label}连接失败，请检查 HEFENG_API_HOST 和网络连接：{exc.reason}') from exc


def _geo_lookup(location):
    api_host = _hefeng_api_host()
    url = (
        f'{api_host}/geo/v2/city/lookup?'
        + urllib.parse.urlencode({'location': location, 'lang': 'zh'})
    )
    data = _open_json(url, '城市查询')
    if data.get('code') != '200' or not data.get('location'):
        raise RuntimeError(f'城市 "{location}" 未找到（code={data.get("code")}），请输入更准确的地名')
    loc = data['location'][0]
    return f'{float(loc["lat"]):.2f}', f'{float(loc["lon"]):.2f}', loc['name'], loc['adm1']


def get_weather(location):
    latitude, longitude, city_name, province = _geo_lookup(location)
    api_host = _hefeng_api_host()
    url = (
        f'{api_host}/weather/v1/current/{latitude}/{longitude}?'
        + urllib.parse.urlencode({'lang': 'zh', 'localTime': 'true'})
    )
    data = _open_json(url, '实时天气')
    if not data.get('condition') or not data.get('wind'):
        raise RuntimeError('实时天气返回数据不完整，请检查和风天气接口权限')
    wind = data['wind']
    return {
        'city': f'{province} {city_name}',
        'temp': data['temperature']['value'],
        'feels_like': data['feelsLike']['value'],
        'text': data['condition']['text'],
        'wind_dir': wind['direction']['compass'],
        'wind_scale': wind['scale'],
        'wind_speed': wind['speed']['value'],
        'wind_gust': data.get('windGust', {}).get('value'),
        'humidity': round(data['humidity'] * 100),
        'vis': round(data['visibility']['value'] / 1000, 1),
        'precip': data.get('precipitation', {}).get('amount', {}).get('value', 0),
        'precip_type': data.get('precipitation', {}).get('type', 'none'),
        'obs_time': data['validTime'],
    }


def get_weather_forecast(location):
    latitude, longitude, city_name, province = _geo_lookup(location)
    api_host = _hefeng_api_host()
    url = (
        f'{api_host}/weather/v1/daily/{latitude}/{longitude}?'
        + urllib.parse.urlencode({'days': 3, 'lang': 'zh', 'localTime': 'true'})
    )
    data = _open_json(url, '天气预报')
    if not data.get('days'):
        raise RuntimeError('天气预报返回数据不完整，请检查和风天气接口权限')
    days = []
    for d in data['days']:
        daytime = d['daytime']
        nighttime = d['nighttime']
        precipitation = daytime.get('precipitation', {})
        days.append({
            'date': daytime['forecastStartTime'][:10],
            'text_day': daytime['condition']['text'],
            'text_night': nighttime['condition']['text'],
            'temp_max': d['temperatureMax']['value'],
            'temp_min': d['temperatureMin']['value'],
            'wind_scale_day': daytime['wind']['scale'],
            'wind_speed_day': daytime['wind']['speed']['value'],
            'wind_gust_day': daytime.get('windGustMax', {}).get('value'),
            'humidity': round(daytime['humidity'] * 100),
            'precip': precipitation.get('amount', {}).get('value', 0),
            'precip_probability': round(precipitation.get('probability', 0) * 100),
            'uv_index': d.get('uvIndexMax'),
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
    cleaned = re.sub(
        r'^(?:请问|查询|看看|评估|帮我查(?:询)?|我想知道)?\s*'
        r'(?:今天|明天|后天|现在|当前|这周末|周末)?\s*'
        r'(?:上午|下午|晚上)?\s*',
        '', question.strip(),
    )
    match = re.match(
        r'([\u4e00-\u9fa5]{2,10}?)'
        r'(?=今天|明天|后天|现在|当前|上午|下午|晚上|这周末|周末|本周|这周|'
        r'天气|风速|适合|能|可以|的|如何|怎样|会|吗|[，。！？?]|$)',
        cleaned,
    )
    if match and not re.search(r'无人机|航拍|穿越机|天气|风速|飞', match.group(1)):
        return match.group(1)
    cleaned = re.sub(
        r'(今天|明天|后天|现在|当前|上午|下午|晚上|这周末|周末|天气|风速|适合|无人机|航拍|穿越机|飞|吗|怎样|如何|多大|[，。！？?])',
        '',
        cleaned,
    ).strip()
    if 2 <= len(cleaned) <= 10 and not re.search(r'能|可以|的|信号|GPS', cleaned):
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
                f'白天风速{day["wind_speed_day"]}m/s，最大阵风{day["wind_gust_day"]}m/s，'
                f'风力{day["wind_scale_day"]}级，湿度{day["humidity"]}%，'
                f'降水量{day["precip"]}mm，降水概率{day["precip_probability"]}%。'
            )
        lines.append('逐日预报未提供能见度，不能据此确认飞行条件安全。')
        return '\n'.join(lines)
    return (
        f'查询地点：{weather_data["city"]}\n'
        f'天气：{weather_data["text"]}\n'
        f'温度：{weather_data["temp"]}℃，体感温度：{weather_data["feels_like"]}℃\n'
        f'风向：{weather_data["wind_dir"]}，风力：{weather_data["wind_scale"]}级，'
        f'风速：{weather_data["wind_speed"]}m/s，阵风：{weather_data["wind_gust"]}m/s\n'
        f'湿度：{weather_data["humidity"]}%，能见度：{weather_data["vis"]}km，'
        f'降水量：{weather_data["precip"]}mm，降水类型：{weather_data["precip_type"]}\n'
        f'观测时间：{weather_data["obs_time"]}'
    )


def weather_agent(question):
    api_key = os.getenv('DASHSCOPE_API_KEY') or getattr(settings, 'DASHSCOPE_API_KEY', '')
    if not api_key:
        raise RuntimeError('缺少 DASHSCOPE_API_KEY，请在 server/.env 中配置千问密钥')
    chat_model = os.getenv('DASHSCOPE_MODEL') or getattr(settings, 'DASHSCOPE_MODEL', '') or 'qwen-plus'
    base_url = os.getenv('DASHSCOPE_BASE_URL') or getattr(settings, 'DASHSCOPE_BASE_URL', '')

    location = _extract_location(question)
    forecast = _needs_forecast(question)
    weather_data = get_weather_forecast(location) if forecast else get_weather(location)
    weather_summary = _rule_based_summary(weather_data, forecast=forecast)

    system_prompt = (
        '你是无人机飞行气象顾问。根据天气数据，结合无人机安全飞行标准给出专业建议：'
        '风速 < 5m/s 适合飞行，5~8m/s 需谨慎，> 8m/s 建议停飞；'
        '能见度 < 1km 禁飞；降水、雷暴天气禁飞；湿度 > 90% 注意电子设备防潮。'
        '回答要给出明确的"适合/谨慎/不适合飞行"结论，并说明原因。优先考虑阵风。'
        '如果预报缺少能见度等关键数据，不得断言飞行安全。'
        '回答结构包含：结论、天气依据、飞行风险、实训操作建议。'
        '结果仅供教学参考，实际飞行须遵守法规、学校制度和现场教师要求。'
    )

    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': f'用户问题：{question}\n\n和风天气数据：\n{weather_summary}'},
    ]

    client = OpenAI(api_key=api_key, base_url=base_url)
    resp = client.chat.completions.create(
        model=chat_model,
        messages=messages,
        temperature=0.2,
        max_tokens=1200,
    )
    content = resp.choices[0].message.content or ''
    if not content:
        raise RuntimeError('千问未返回天气评估内容')
    return f'{content}\n\n天气数据来源：和风天气（https://www.qweather.com/）'
