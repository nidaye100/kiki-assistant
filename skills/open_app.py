"""
skills/open_app.py
根据 target 打开对应应用程序
支持通过 config/apps.json 自定义路径映射
"""

import os
import json
import logging
import subprocess

logger = logging.getLogger("kiki.skill.open_app")

# 默认应用路径（Windows），可在 config/apps.json 中覆盖
DEFAULT_APPS = {
    "qq":           r"C:\Program Files\Tencent\QQNT\QQ.exe",
    "微信":          r"C:\Program Files\Tencent\WeChat\WeChat.exe",
    "记事本":        "notepad.exe",
    "浏览器":        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "chrome":       r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "资源管理器":    "explorer.exe",
    "计算器":        "calc.exe",
}

_APPS_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "config", "apps.json"
)


def _load_apps() -> dict:
    apps = dict(DEFAULT_APPS)
    if os.path.exists(_APPS_CONFIG_PATH):
        with open(_APPS_CONFIG_PATH, "r", encoding="utf-8") as f:
            custom = json.load(f)
        apps.update(custom)
    return apps


def handle(intent: dict):
    target = intent.get("target", "").lower().strip()
    apps = _load_apps()

    # 模糊匹配：target 作为子串
    matched_path = None
    for key, path in apps.items():
        if target in key or key in target:
            matched_path = path
            break

    if not matched_path:
        msg = f"未找到应用: {target}，请在 config/apps.json 中添加路径"
        logger.warning(msg)
        _speak(msg)
        return

    try:
        subprocess.Popen([matched_path], shell=True)
        msg = f"正在打开 {target}"
        logger.info(msg)
        _speak(msg)
    except Exception as e:
        msg = f"打开 {target} 失败: {e}"
        logger.error(msg)
        _speak(msg)


def _speak(text: str):
    print(f"\n[Kiki] {text}\n")
