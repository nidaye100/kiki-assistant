"""
core/wake_word.py
使用 Porcupine 实现本地低功耗唤醒词检测
"""

import os
import struct
import logging
import pvporcupine
import pyaudio

logger = logging.getLogger("kiki.wake_word")


class WakeWordDetector:
    """
    Porcupine 唤醒词检测器
    支持内置关键词 (hey google / picovoice 等) 或自定义 .ppn 模型
    """

    def __init__(self):
        self._running = False

        # 优先使用自定义 .ppn 唤醒词模型，否则回退内置 'picovoice'
        ppn_path = os.path.join(
            os.path.dirname(__file__), "..", "config", "kiki_windows.ppn"
        )

        access_key = os.environ.get("PORCUPINE_ACCESS_KEY", "")
        if not access_key:
            raise EnvironmentError(
                "请在环境变量 PORCUPINE_ACCESS_KEY 中填写 Picovoice 访问密钥\n"
                "免费申请地址: https://console.picovoice.ai/"
            )

        if os.path.exists(ppn_path):
            self._porcupine = pvporcupine.create(
                access_key=access_key,
                keyword_paths=[ppn_path],
            )
            logger.info(f"已加载自定义唤醒词模型: {ppn_path}")
        else:
            # 使用内置关键词作为占位（实际部署请替换为自定义 'Kiki' 模型）
            self._porcupine = pvporcupine.create(
                access_key=access_key,
                keywords=["picovoice"],  # 替换为 'Kiki' 自定义模型后删除此行
            )
            logger.warning("未找到 kiki_windows.ppn，使用内置关键词（仅供测试）")

        self._pa = pyaudio.PyAudio()
        self._stream = self._pa.open(
            rate=self._porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self._porcupine.frame_length,
        )
        self._running = True

    def wait_for_wake_word(self):
        """阻塞直到检测到唤醒词"""
        while self._running:
            pcm = self._stream.read(
                self._porcupine.frame_length, exception_on_overflow=False
            )
            pcm = struct.unpack_from("h" * self._porcupine.frame_length, pcm)
            result = self._porcupine.process(pcm)
            if result >= 0:
                return True
        return False

    def stop(self):
        self._running = False
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
        if self._pa:
            self._pa.terminate()
        if self._porcupine:
            self._porcupine.delete()
        logger.info("唤醒词检测器已停止")
