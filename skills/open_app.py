"""
skills/open_app.py
自动发现系统中安装的应用程序，无需手动配置路径
查找顺序：
  1. Windows 注册表（HKLM + HKCU，覆盖 99% 的正规安装软件）
  2. 开始菜单快捷方式扫描（.lnk 文件）
  3. Program Files 目录暴力扫描
  4. 内置已知路径兜底
"""

import os
import glob
import logging
import subprocess
import winreg

logger = logging.getLogger("kiki.skill.open_app")

# ── 内置别名表：中文/常用名 → 可能的 exe 名称（支持多候选）──────────────
# 这里只是"名字到exe的映射"，实际路径完全自动查找
APP_ALIASES: dict[str, list[str]] = {
    # 通讯
    "qq":        ["QQ.exe", "QQ", "qq.exe"],
    "微信":       ["WeChat.exe", "Weixin.exe"],
    "钉钉":       ["DingTalk.exe"],
    "飞书":       ["Feishu.exe", "LarkShell.exe"],
    "telegram":  ["Telegram.exe"],
    "discord":   ["Discord.exe", "Update.exe"],

    # 浏览器
    "浏览器":     ["chrome.exe", "msedge.exe", "firefox.exe", "BraveBrowser.exe"],
    "chrome":    ["chrome.exe"],
    "edge":      ["msedge.exe"],
    "firefox":   ["firefox.exe"],

    # 开发
    "vscode":    ["Code.exe"],
    "vs code":   ["Code.exe"],
    "idea":      ["idea64.exe", "idea.exe"],
    "pycharm":   ["pycharm64.exe", "pycharm.exe"],

    # 游戏
    "steam":     ["steam.exe"],
    "minecraft": ["javaw.exe", "Minecraft.exe", "MinecraftLauncher.exe"],

    # 系统内置（直接调用，无需查找）
    "记事本":     ["notepad.exe"],
    "计算器":     ["calc.exe"],
    "资源管理器":  ["explorer.exe"],
    "画图":       ["mspaint.exe"],
    "任务管理器":  ["taskmgr.exe"],
    "控制面板":   ["control.exe"],

    # 办公
    "word":      ["WINWORD.EXE"],
    "excel":     ["EXCEL.EXE"],
    "ppt":       ["POWERPNT.EXE"],
    "powerpoint":["POWERPNT.EXE"],
    "wps":       ["wps.exe", "WPS.exe"],

    # 媒体
    "网易云":     ["cloudmusic.exe"],
    "酷狗":       ["KGMusic.exe", "kugou.exe"],
    "potplayer":  ["PotPlayerMini64.exe", "PotPlayerMini.exe"],
    "vlc":        ["vlc.exe"],
}

# ── Windows 系统内置命令，直接执行无需查找路径 ──────────────────────────
BUILTIN_COMMANDS = {
    "notepad.exe", "calc.exe", "explorer.exe",
    "mspaint.exe", "taskmgr.exe", "control.exe",
    "cmd.exe", "powershell.exe", "mmc.exe",
}


def handle(intent: dict):
    target = intent.get("target", "").lower().strip()
    if not target:
        _speak("请告诉我要打开哪个应用")
        return

    # 1. 找到候选 exe 列表
    exe_candidates = _resolve_candidates(target)
    if not exe_candidates:
        _speak(f"没有找到「{target}」的相关应用")
        logger.warning(f"无法解析应用名: {target}")
        return

    # 2. 依次查找实际路径
    for exe_name in exe_candidates:
        # 系统内置，直接执行
        if exe_name.lower() in BUILTIN_COMMANDS:
            _launch(exe_name, target)
            return

        path = _find_executable(exe_name)
        if path:
            _launch(path, target)
            return

    _speak(f"找到了「{target}」的程序名，但在你的电脑上没有安装")


def _resolve_candidates(target: str) -> list[str]:
    """将用户说的名字转换为 exe 文件名候选列表"""
    # 精确匹配别名表
    for alias, exes in APP_ALIASES.items():
        if alias in target or target in alias:
            return exes

    # 没找到别名，尝试直接当 exe 名用（用户可能说了准确名字）
    guesses = [target + ".exe", target.capitalize() + ".exe"]
    return guesses


def _find_executable(exe_name: str) -> str | None:
    """
    多源查找 exe 路径
    返回找到的完整路径，找不到返回 None
    """
    # 方法1：注册表 App Paths（最准，覆盖主流软件）
    path = _search_registry_app_paths(exe_name)
    if path:
        return path

    # 方法2：注册表已安装软件列表
    path = _search_registry_uninstall(exe_name)
    if path:
        return path

    # 方法3：开始菜单快捷方式
    path = _search_start_menu(exe_name)
    if path:
        return path

    # 方法4：Program Files 目录扫描
    path = _search_program_files(exe_name)
    if path:
        return path

    return None


def _search_registry_app_paths(exe_name: str) -> str | None:
    """查找 HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths"""
    key_path = f"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\{exe_name}"
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            with winreg.OpenKey(hive, key_path) as key:
                path, _ = winreg.QueryValueEx(key, "")
                if path and os.path.exists(path):
                    logger.debug(f"注册表 AppPaths 找到: {path}")
                    return path
        except FileNotFoundError:
            continue
        except Exception as e:
            logger.debug(f"注册表查询异常: {e}")
    return None


def _search_registry_uninstall(exe_name: str) -> str | None:
    """
    扫描卸载注册表，从 InstallLocation 拼接 exe 路径
    覆盖大量标准安装程序
    """
    uninstall_paths = [
        "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall",
        "SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall",
    ]
    exe_lower = exe_name.lower()

    for reg_path in uninstall_paths:
        for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                with winreg.OpenKey(hive, reg_path) as key:
                    count = winreg.QueryInfoKey(key)[0]
                    for i in range(count):
                        try:
                            sub_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, sub_name) as sub:
                                try:
                                    loc, _ = winreg.QueryValueEx(sub, "InstallLocation")
                                    if loc:
                                        candidate = os.path.join(loc, exe_name)
                                        if os.path.exists(candidate):
                                            logger.debug(f"注册表卸载表找到: {candidate}")
                                            return candidate
                                except FileNotFoundError:
                                    pass
                        except Exception:
                            continue
            except Exception:
                continue
    return None


def _search_start_menu(exe_name: str) -> str | None:
    """
    扫描开始菜单 .lnk 快捷方式，解析目标路径
    """
    start_menu_dirs = [
        os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
        os.path.expandvars(r"%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs"),
    ]
    exe_lower = exe_name.lower().replace(".exe", "")

    for smd in start_menu_dirs:
        if not os.path.exists(smd):
            continue
        for lnk in glob.glob(os.path.join(smd, "**", "*.lnk"), recursive=True):
            lnk_name = os.path.splitext(os.path.basename(lnk))[0].lower()
            if exe_lower in lnk_name or lnk_name in exe_lower:
                target_path = _resolve_lnk(lnk)
                if target_path and os.path.exists(target_path):
                    logger.debug(f"开始菜单快捷方式找到: {target_path}")
                    return target_path
    return None


def _resolve_lnk(lnk_path: str) -> str | None:
    """用 PowerShell 解析 .lnk 快捷方式的目标路径"""
    try:
        cmd = (
            f'powershell -NoProfile -Command "'
            f'$sh=New-Object -ComObject WScript.Shell;'
            f'$sc=$sh.CreateShortcut(\\"{lnk_path}\\");'
            f'Write-Output $sc.TargetPath"'
        )
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
        path = result.stdout.strip()
        return path if path else None
    except Exception:
        return None


def _search_program_files(exe_name: str) -> str | None:
    """最后手段：暴力扫描 Program Files"""
    search_roots = [
        os.environ.get("ProgramFiles", r"C:\Program Files"),
        os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs"),
    ]
    for root in search_roots:
        if not root or not os.path.exists(root):
            continue
        matches = glob.glob(
            os.path.join(root, "**", exe_name), recursive=True
        )
        if matches:
            logger.debug(f"Program Files 扫描找到: {matches[0]}")
            return matches[0]
    return None


def _launch(path: str, name: str):
    try:
        subprocess.Popen([path], shell=True)
        msg = f"正在打开{name}"
        logger.info(f"{msg} → {path}")
        _speak(msg)
    except Exception as e:
        _speak(f"打开{name}失败: {e}")
        logger.error(e)


def _speak(text: str):
    print(f"\n[Kiki] {text}\n")
