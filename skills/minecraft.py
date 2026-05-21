"""
skills/minecraft.py
控制本地 Minecraft 服务器
支持启动 / 停止 / 状态查询 / 发送控制台指令

使用方法：
  Kiki，启动服务器
  Kiki，关闭服务器
  Kiki，服务器状态
  Kiki，服务器执行 say Hello
"""

import os
import logging
import subprocess
import socket

logger = logging.getLogger("kiki.skill.minecraft")

# ─── 配置区（根据实际情况修改）──────────────────────────────────────
# 服务器 jar 路径
MC_JAR = os.environ.get(
    "MC_JAR_PATH",
    r"C:\MinecraftServer\server.jar"   # ← 修改为实际路径
)
MC_DIR = os.path.dirname(MC_JAR)      # 服务器工作目录
MC_JAVA_ARGS = "-Xmx2G -Xms1G"       # JVM 参数，按内存酌情调整

# RCON 配置（如需发送控制台指令，需在 server.properties 开启 rcon）
RCON_HOST = "127.0.0.1"
RCON_PORT = int(os.environ.get("MC_RCON_PORT", 25575))
RCON_PASSWORD = os.environ.get("MC_RCON_PASSWORD", "")

# 检测服务器是否在线：尝试连接游戏端口
MC_GAME_PORT = int(os.environ.get("MC_GAME_PORT", 25565))
# ────────────────────────────────────────────────────────────────────

_server_process: subprocess.Popen | None = None


def handle_start(intent: dict):
    global _server_process
    if _is_running():
        _speak("服务器已经在运行中")
        return

    if not os.path.exists(MC_JAR):
        _speak(f"找不到服务器文件: {MC_JAR}，请检查 MC_JAR_PATH 配置")
        return

    try:
        cmd = f'java {MC_JAVA_ARGS} -jar "{MC_JAR}" nogui'
        _server_process = subprocess.Popen(
            cmd,
            cwd=MC_DIR,
            shell=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE,  # Windows 独立窗口
        )
        msg = "Minecraft 服务器已启动"
        logger.info(f"{msg}  PID={_server_process.pid}")
        _speak(msg)
    except Exception as e:
        _speak(f"启动服务器失败: {e}")
        logger.error(e)


def handle_stop(intent: dict):
    if not _is_running():
        _speak("服务器当前未运行")
        return

    # 优先用 RCON 发送 stop 指令（优雅关闭）
    if RCON_PASSWORD:
        success = _send_rcon("stop")
        if success:
            _speak("已发送 stop 指令，服务器正在关闭")
            return

    # 回退：直接终止进程
    global _server_process
    if _server_process:
        _server_process.terminate()
        _server_process = None
    _speak("Minecraft 服务器已强制停止")
    logger.info("服务器已停止")


def handle_status(intent: dict):
    online = _is_running()
    if online:
        _speak("服务器正在运行，状态正常")
    else:
        _speak("服务器当前未运行")
    logger.info(f"服务器状态: {'在线' if online else '离线'}")


def handle_cmd(intent: dict):
    """向 RCON 发送任意控制台指令"""
    cmd = intent.get("target", "").strip()
    if not cmd:
        _speak("请告诉我要执行什么指令")
        return

    if not RCON_PASSWORD:
        _speak("未配置 RCON 密码，无法发送指令。请在 server.properties 中开启 rcon 并设置环境变量 MC_RCON_PASSWORD")
        return

    success = _send_rcon(cmd)
    if success:
        _speak(f"已执行指令: {cmd}")
    else:
        _speak(f"指令发送失败，请确认服务器已启动且 RCON 已开启")


# ─── 内部工具函数 ───────────────────────────────────────────────────

def _is_running() -> bool:
    """通过尝试连接游戏端口判断服务器是否在线"""
    try:
        with socket.create_connection((RCON_HOST, MC_GAME_PORT), timeout=1):
            return True
    except OSError:
        return False


def _send_rcon(command: str) -> bool:
    """
    简易 RCON 实现（Source RCON Protocol）
    需要在 server.properties 设置：
        rcon.port=25575
        rcon.password=<你的密码>
        enable-rcon=true
    """
    import struct

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((RCON_HOST, RCON_PORT))

        def send_packet(req_id: int, ptype: int, payload: str):
            data = payload.encode("utf-8") + b"\x00\x00"
            header = struct.pack("<iii", len(data) + 8, req_id, ptype)
            sock.sendall(header + data)

        def recv_packet():
            raw_len = sock.recv(4)
            length = struct.unpack("<i", raw_len)[0]
            data = b""
            while len(data) < length:
                data += sock.recv(length - len(data))
            return struct.unpack("<ii", data[:8]), data[8:-2].decode("utf-8")

        # 认证
        send_packet(1, 3, RCON_PASSWORD)
        _, _ = recv_packet()

        # 发送指令
        send_packet(2, 2, command)
        _, response = recv_packet()
        logger.info(f"RCON 响应: {response}")
        sock.close()
        return True

    except Exception as e:
        logger.error(f"RCON 错误: {e}")
        return False


def _speak(text: str):
    print(f"\n[Kiki] {text}\n")
