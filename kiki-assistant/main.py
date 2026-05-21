"""
Kiki Assistant - 主入口
启动唤醒词监听 → 语音识别 → 意图解析 → 命令执行
"""

import sys
import signal
import logging
from core.wake_word import WakeWordDetector
from core.speech_recognizer import SpeechRecognizer
from core.intent_parser import IntentParser
from core.command_router import CommandRouter

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("kiki")


def main():
    logger.info("🎙️ Kiki 正在启动...")

    wake = WakeWordDetector()
    recognizer = SpeechRecognizer()
    parser = IntentParser()
    router = CommandRouter()

    def shutdown(sig, frame):
        logger.info("👋 Kiki 已关闭")
        wake.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    logger.info("✅ 就绪，等待唤醒词 'Kiki'...")

    while True:
        # 1. 等待唤醒
        wake.wait_for_wake_word()
        logger.info("⚡ 检测到唤醒词！")

        # 2. 录音识别
        text = recognizer.listen_and_recognize()
        if not text:
            logger.warning("未识别到有效指令")
            continue
        logger.info(f"📝 识别结果：{text}")

        # 3. 解析意图
        intent = parser.parse(text)
        logger.info(f"🧠 意图：{intent}")

        # 4. 路由执行
        router.execute(intent, text)


if __name__ == "__main__":
    main()
