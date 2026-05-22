"""
skills/weather.py
调用 wttr.in 公开接口获取天气，无需 API Key
"""

import logging
import requests

logger = logging.getLogger("kiki.skill.weather")

# 默认城市，可在 config/settings.py 中覆盖
DEFAULT_CITY = "Toyama"


def handle(intent: dict):
    city = intent.get("target", "") or DEFAULT_CITY

    # wttr.in 支持中文城市名
    url = f"https://wttr.in/{city}?format=3&lang=zh"
    try:
        resp = requests.get(url, timeout=8)
        resp.encoding = "utf-8"
        result = resp.text.strip()
        logger.info(f"🌤️ 天气查询结果: {result}")
        _speak(result)
    except requests.RequestException as e:
        msg = f"天气查询失败: {e}"
        logger.error(msg)
        _speak(msg)


def _speak(text: str):
    """简单打印，后续可接入 TTS"""
    print(f"\n[Kiki] {text}\n")
