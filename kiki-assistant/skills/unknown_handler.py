"""
skills/unknown_handler.py
处理无法识别的指令：
  1. 调用 Ollama 尝试生成新技能脚本
  2. 弹窗让用户审核代码
  3. 审核通过后保存到 learned_scripts/，并更新 skills.json
"""

import os
import json
import logging
import tkinter as tk
from tkinter import scrolledtext, messagebox
import requests

logger = logging.getLogger("kiki.skill.unknown")

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3:4b"

LEARNED_DIR = os.path.join(os.path.dirname(__file__), "..", "learned_scripts")
SKILLS_INDEX = os.path.join(os.path.dirname(__file__), "..", "config", "learned_skills.json")

CODE_GENERATION_SYSTEM = """你是一个 Python 脚本生成助手。
用户会描述一个电脑操作，你需要生成一个安全的 Python 函数来完成这个操作。

规则：
1. 只生成一个名为 handle(intent: dict) 的函数
2. 不要使用 shutil.rmtree、os.system("format")、subprocess 删除系统文件等危险操作
3. 代码要有注释
4. 只返回 Python 代码，不要 markdown 代码块，不要解释

示例输出：
def handle(intent: dict):
    # 打开计算器
    import subprocess
    subprocess.Popen("calc.exe")
    print("[Kiki] 已打开计算器")
"""


def handle(intent: dict):
    original = intent.get("extra", "") or intent.get("target", "")
    if not original:
        _speak("我没有听清楚，请再说一遍")
        return

    logger.info(f"未知指令: {original}，尝试生成新技能...")
    _speak(f"我不太明白「{original}」，让我想想...")

    code = _generate_code(original)
    if not code:
        _speak("抱歉，我也不知道怎么做这个")
        return

    # 弹窗审核
    approved, script_name = _review_code(original, code)
    if approved and script_name:
        _save_skill(script_name, original, code)
        _speak(f"好的，我学会了「{original}」，下次直接说就行")
    else:
        _speak("好的，这个技能我先不保存")


def _generate_code(task: str) -> str:
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "system": CODE_GENERATION_SYSTEM,
                "prompt": f"任务描述：{task}",
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 400},
            },
            timeout=30,
        )
        code = resp.json().get("response", "").strip()
        # 去除可能的 markdown
        code = code.replace("```python", "").replace("```", "").strip()
        return code
    except Exception as e:
        logger.error(f"代码生成失败: {e}")
        return ""


def _review_code(task: str, code: str) -> tuple[bool, str]:
    """弹出 Tkinter 审核窗口，返回 (是否确认, 脚本名)"""
    result = {"approved": False, "name": ""}

    root = tk.Tk()
    root.title("🔍 Kiki 发现了新技能 - 请审核")
    root.geometry("700x520")
    root.resizable(True, True)

    tk.Label(
        root,
        text=f"任务: {task}",
        font=("Microsoft YaHei", 12, "bold"),
        fg="#2c3e50",
    ).pack(pady=(14, 4))
    tk.Label(
        root,
        text="⚠️  请仔细检查代码安全性，确认无误后点击「保存技能」",
        font=("Microsoft YaHei", 10),
        fg="#e67e22",
    ).pack(pady=(0, 8))

    txt = scrolledtext.ScrolledText(root, font=("Consolas", 10), height=18)
    txt.insert(tk.END, code)
    txt.pack(fill=tk.BOTH, expand=True, padx=14, pady=4)

    name_frame = tk.Frame(root)
    name_frame.pack(fill=tk.X, padx=14, pady=6)
    tk.Label(name_frame, text="技能名称:", font=("Microsoft YaHei", 10)).pack(side=tk.LEFT)
    name_var = tk.StringVar(value=task[:20].replace(" ", "_"))
    name_entry = tk.Entry(name_frame, textvariable=name_var, width=30)
    name_entry.pack(side=tk.LEFT, padx=6)

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=10)

    def approve():
        result["approved"] = True
        result["name"] = name_var.get().strip() or "custom_skill"
        root.destroy()

    def reject():
        root.destroy()

    tk.Button(
        btn_frame, text="✅ 保存技能", command=approve,
        bg="#27ae60", fg="white", font=("Microsoft YaHei", 10, "bold"),
        padx=16, pady=6,
    ).pack(side=tk.LEFT, padx=10)
    tk.Button(
        btn_frame, text="❌ 不保存", command=reject,
        bg="#c0392b", fg="white", font=("Microsoft YaHei", 10),
        padx=16, pady=6,
    ).pack(side=tk.LEFT, padx=10)

    root.mainloop()
    return result["approved"], result["name"]


def _save_skill(name: str, task: str, code: str):
    os.makedirs(LEARNED_DIR, exist_ok=True)
    filename = f"{name}.py"
    filepath = os.path.join(LEARNED_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f'"""自动生成技能: {task}"""\n\n')
        f.write(code)

    # 更新技能索引
    index = {}
    if os.path.exists(SKILLS_INDEX):
        with open(SKILLS_INDEX, "r", encoding="utf-8") as f:
            index = json.load(f)
    index[task] = filename

    with open(SKILLS_INDEX, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    logger.info(f"✅ 新技能已保存: {filepath}")


def _speak(text: str):
    print(f"\n[Kiki] {text}\n")
