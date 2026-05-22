"""
core/intent_parser.py
调用本地 Ollama（Qwen3）将自然语言解析为标准 JSON 意图
"""

import json
import logging
import requests

logger = logging.getLogger("kiki.intent")

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3:4b"

SYSTEM_PROMPT = """你是一个命令解析器。只返回 JSON，不要有任何解释或 markdown 代码块。

支持的意图列表：
- weather       查询天气
- open_app      打开应用程序
- search_web    搜索网页
- mc_start      启动 Minecraft 服务器
- mc_stop       关闭 Minecraft 服务器
- mc_status     查询 Minecraft 服务器状态
- mc_cmd        向 Minecraft 服务器发送控制台指令
- file_op       文件操作
- unknown       无法识别的指令

返回格式示例（只返回这个 JSON，不要其他内容）：
{"intent": "weather", "target": "today", "extra": ""}
{"intent": "open_app", "target": "qq", "extra": ""}
{"intent": "mc_cmd", "target": "say Hello", "extra": ""}
{"intent": "unknown", "target": "", "extra": "原始文本"}

字段说明：
- intent: 必填，从上面列表选一个
- target: 操作对象，没有则留空字符串
- extra: 附加信息，没有则留空字符串
"""


class IntentParser:
    def __init__(self):
        self._check_ollama()

    def _check_ollama(self):
        try:
            r = requests.get("http://localhost:11434/", timeout=3)
            if r.status_code == 200:
                logger.info("✅ Ollama 连接正常")
        except Exception:
            logger.warning(
                "⚠️ 无法连接 Ollama，请确认已启动: ollama serve\n"
                "   并已下载模型: ollama pull qwen3:4b"
            )

    def parse(self, text: str) -> dict:
        """
        将自然语言文本解析为意图字典
        返回: {"intent": str, "target": str, "extra": str}
        """
        prompt = f"用户说：{text}"
        try:
            resp = requests.post(
                OLLAMA_URL,
                json={
                    "model": MODEL,
                    "prompt": prompt,
                    "system": SYSTEM_PROMPT,
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": 100},
                },
                timeout=15,
            )
            raw = resp.json().get("response", "").strip()
            logger.debug(f"Ollama 原始输出: {raw}")

            # 清理可能的 markdown fence
            raw = raw.replace("```json", "").replace("```", "").strip()

            intent = json.loads(raw)
            # 校验必须字段
            assert "intent" in intent
            intent.setdefault("target", "")
            intent.setdefault("extra", "")
            return intent

        except json.JSONDecodeError:
            logger.error(f"意图解析失败，原始输出无法解析为 JSON: {raw!r}")
        except Exception as e:
            logger.error(f"意图解析出错: {e}")

        return {"intent": "unknown", "target": "", "extra": text}
