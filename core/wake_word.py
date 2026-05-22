"""
core/wake_word.py
使用 openWakeWord 实现本地唤醒词检测
完全本地运行，无需注册任何账号，无需 API Key
支持中日英（"Kiki" 发音在三种语言中基本一致）
"""

import logging
import numpy as np
import pyaudio
from openwakeword.model import Model

logger = logging.getLogger("kiki.wake_word")

# 音频参数
RATE = 16000
CHUNK = 1280  # openWakeWord 推荐帧大小

# 检测阈值：0.0~1.0，越高越严格，越低越灵敏
# 建议 0.5~0.7，太低容易误触发
THRESHOLD = 0.5

# 使用内置的 "hey jarvis" 模型作为唤醒词
# 发音近似 "Kiki" 的替代；也可以自训练模型放入 config/
# 完整内置模型列表：https://github.com/dscripka/openWakeWord#pre-trained-models
WAKE_WORD_MODEL = "hey_jarvis"


class WakeWordDetector:
    """
    基于 openWakeWord 的本地唤醒词检测器
    零注册、零配置、完全离线
    """

    def __init__(self):
        logger.info(f"正在加载唤醒词模型: {WAKE_WORD_MODEL} ...")
        self._model = Model(
            wakeword_models=[WAKE_WORD_MODEL],
            inference_framework="onnx",
        )
        self._pa = pyaudio.PyAudio()
        self._stream = self._pa.open(
            rate=RATE,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=CHUNK,
        )
        self._running = True
        logger.info(f"✅ 唤醒词模型加载完成，阈值: {THRESHOLD}")

    def wait_for_wake_word(self) -> bool:
        """阻塞直到检测到唤醒词，返回 True"""
        while self._running:
            try:
                raw = self._stream.read(CHUNK, exception_on_overflow=False)
                audio = np.frombuffer(raw, dtype=np.int16)
                prediction = self._model.predict(audio)

                score = prediction.get(WAKE_WORD_MODEL, 0.0)
                if score >= THRESHOLD:
                    logger.info(f"✅ 检测到唤醒词，置信度: {score:.2f}")
                    # 重置模型状态，避免连续触发
                    self._model.reset()
                    return True

            except Exception as e:
                logger.debug(f"唤醒词监听循环异常（通常无害）: {e}")
                continue

        return False

    def stop(self):
        self._running = False
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
        if self._pa:
            self._pa.terminate()
        logger.info("唤醒词检测器已停止")
