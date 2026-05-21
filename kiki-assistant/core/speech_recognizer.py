"""
core/speech_recognizer.py
使用 faster-whisper 本地语音识别（比原版 Whisper 快 4x）
"""

import io
import wave
import logging
import pyaudio
from faster_whisper import WhisperModel

logger = logging.getLogger("kiki.speech")

# 录音参数
RATE = 16000
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK = 1024
SILENCE_THRESHOLD = 500   # 静音阈值（振幅）
SILENCE_DURATION = 1.5    # 静音超过此秒数则停止录音
MAX_DURATION = 10         # 最长录音时间（秒）


class SpeechRecognizer:
    def __init__(self, model_size: str = "small"):
        logger.info(f"正在加载 Whisper 模型: {model_size} ...")
        # device="cpu" 适合普通家用电脑；有 NVIDIA GPU 可改为 "cuda"
        self._model = WhisperModel(model_size, device="cpu", compute_type="int8")
        self._pa = pyaudio.PyAudio()
        logger.info("✅ Whisper 模型加载完成")

    def listen_and_recognize(self) -> str:
        """录音并返回识别文本"""
        audio_data = self._record()
        if not audio_data:
            return ""
        return self._transcribe(audio_data)

    def _record(self) -> bytes:
        """录制音频直到静音"""
        stream = self._pa.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
        )

        logger.info("🎤 开始录音...")
        frames = []
        silent_chunks = 0
        max_silent_chunks = int(RATE / CHUNK * SILENCE_DURATION)
        max_chunks = int(RATE / CHUNK * MAX_DURATION)

        for _ in range(max_chunks):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)

            # 简单振幅检测静音
            amplitude = max(abs(int.from_bytes(data[i:i+2], 'little', signed=True))
                            for i in range(0, len(data), 2))
            if amplitude < SILENCE_THRESHOLD:
                silent_chunks += 1
                if silent_chunks >= max_silent_chunks and len(frames) > 10:
                    break
            else:
                silent_chunks = 0

        stream.stop_stream()
        stream.close()
        logger.info(f"录音结束，共 {len(frames)} 帧")

        if len(frames) < 5:
            return b""

        # 转为 WAV bytes
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(self._pa.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b"".join(frames))
        return buf.getvalue()

    def _transcribe(self, audio_bytes: bytes) -> str:
        """将 WAV bytes 转为文字"""
        buf = io.BytesIO(audio_bytes)
        segments, info = self._model.transcribe(buf, language="zh", beam_size=5)
        text = "".join(seg.text for seg in segments).strip()
        logger.info(f"识别语言: {info.language}  文本: {text}")
        return text
