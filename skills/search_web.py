"""
skills/search_web.py
在默认浏览器中打开搜索结果
"""

import logging
import webbrowser
from urllib.parse import quote

logger = logging.getLogger("kiki.skill.search_web")

SEARCH_ENGINE = "https://www.bing.com/search?q={}"  # 可改为 Google


def handle(intent: dict):
    query = intent.get("target", "") or intent.get("extra", "")
    if not query:
        _speak("请告诉我你要搜索什么")
        return

    url = SEARCH_ENGINE.format(quote(query))
    webbrowser.open(url)
    msg = f"已搜索: {query}"
    logger.info(msg)
    _speak(msg)


def _speak(text: str):
    print(f"\n[Kiki] {text}\n")
