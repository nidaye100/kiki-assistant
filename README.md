# 🎙️ Kiki Assistant

> 一个完全本地运行的中文语音助手，专为 Windows 家用电脑设计。  
> 支持唤醒词激活、语音识别、AI 意图解析、Minecraft 服务器控制，以及人工审核的自学习技能系统。

---

## ✨ 功能特性

| 功能 | 说明 |
|------|------|
| 🔊 **唤醒词检测** | 基于 Porcupine，CPU 占用极低，持续后台监听 |
| 🎤 **语音识别** | 基于 Faster-Whisper（small 模型），本地运行，支持中文 |
| 🧠 **AI 意图解析** | 调用本地 Ollama（Qwen3），严格输出标准 JSON，不自由发挥 |
| 🌤️ **天气查询** | 直接调用 wttr.in 接口，无需 API Key |
| 📂 **打开应用** | 通过 `config/apps.json` 配置应用路径 |
| 🔍 **网页搜索** | 自动打开浏览器搜索指定内容 |
| ⛏️ **Minecraft 控制** | 启动 / 停止 / 状态查询 / RCON 控制台指令 |
| 🧪 **技能自学习** | 遇到未知指令时 AI 生成代码，**必须经用户审核才保存** |

---

## 🖥️ 系统要求

- **操作系统**: Windows 10 / 11（64位）
- **Python**: 3.10 或以上
- **内存**: 建议 8GB 以上（Ollama 模型需要 4~6GB）
- **磁盘**: 约 5GB（含 Whisper 模型 + Ollama 模型）
- **麦克风**: 任意可用麦克风

---

## 🗂️ 目录结构

```
kiki-assistant/
├── main.py                  # 主入口，启动整个助手
├── requirements.txt         # Python 依赖
├── .env.example             # 环境变量模板
├── .gitignore
│
├── core/                    # 核心模块
│   ├── wake_word.py         # 唤醒词检测（Porcupine）
│   ├── speech_recognizer.py # 语音识别（Faster-Whisper）
│   ├── intent_parser.py     # 意图解析（Ollama + Qwen3）
│   └── command_router.py    # 意图路由器
│
├── skills/                  # 内置技能
│   ├── weather.py           # 天气查询
│   ├── open_app.py          # 打开应用
│   ├── search_web.py        # 网页搜索
│   ├── minecraft.py         # Minecraft 服务器控制
│   └── unknown_handler.py   # 未知指令处理 + 技能生成审核
│
├── learned_scripts/         # 自动学习的技能脚本（人工审核后保存）
│   └── .gitkeep
│
└── config/
    ├── apps.json            # 应用路径自定义配置
    ├── learned_skills.json  # 已学习技能的索引（自动生成）
    └── kiki_windows.ppn     # 自定义唤醒词模型（需自行训练）
```

---

## ⚙️ 安装流程

### 第一步：克隆项目

```bash
git clone https://github.com/你的用户名/kiki-assistant.git
cd kiki-assistant
```

### 第二步：安装 Python 依赖

```bash
pip install -r requirements.txt
```

> 如果 `pyaudio` 安装失败，请先安装编译工具：
> ```bash
> pip install pipwin
> pipwin install pyaudio
> ```

### 第三步：安装 Ollama 并下载模型

1. 前往 [https://ollama.com/download](https://ollama.com/download) 下载并安装 Ollama
2. 下载 Qwen3 模型（4B 适合普通电脑）：

```bash
ollama pull qwen3:4b
```

3. 启动 Ollama 服务（会自动在后台运行）：

```bash
ollama serve
```

### 第四步：申请 Porcupine 密钥

1. 前往 [https://console.picovoice.ai/](https://console.picovoice.ai/) 注册免费账号
2. 在 Dashboard 获取 **Access Key**
3. 复制 `.env.example` 为 `.env`，填入密钥：

```bash
copy .env.example .env
```

编辑 `.env`：

```
PORCUPINE_ACCESS_KEY=你的密钥
```

### 第五步：配置环境变量

Windows 系统环境变量设置方式（任选一种）：

**方式 A：临时（当前命令行生效）**
```cmd
set PORCUPINE_ACCESS_KEY=你的密钥
```

**方式 B：永久（推荐）**  
右键"此电脑" → 属性 → 高级系统设置 → 环境变量 → 新建用户变量

### 第六步：配置应用路径

编辑 `config/apps.json`，填写你电脑上实际的应用路径：

```json
{
  "qq": "C:\\Program Files\\Tencent\\QQNT\\QQ.exe",
  "微信": "C:\\Program Files\\Tencent\\WeChat\\WeChat.exe"
}
```

### 第七步：配置 Minecraft 服务器（可选）

编辑 `.env`，填写服务器路径：

```
MC_JAR_PATH=D:\MinecraftServer\server.jar
MC_GAME_PORT=25565
MC_RCON_PORT=25575
MC_RCON_PASSWORD=你的rcon密码
```

在 `server.properties` 中开启 RCON：

```properties
enable-rcon=true
rcon.port=25575
rcon.password=你的rcon密码
```

---

## 🚀 运行

```bash
python main.py
```

看到以下输出表示启动成功：

```
[HH:MM:SS] INFO kiki: 🎙️ Kiki 正在启动...
[HH:MM:SS] INFO kiki.wake_word: ✅ 已加载唤醒词模型
[HH:MM:SS] INFO kiki.speech: ✅ Whisper 模型加载完成
[HH:MM:SS] INFO kiki.intent: ✅ Ollama 连接正常
[HH:MM:SS] INFO kiki: ✅ 就绪，等待唤醒词 'Kiki'...
```

---

## 💬 支持的指令示例

| 你说的话 | 触发的技能 |
|----------|------------|
| Kiki，今天天气怎么样 | 天气查询（富山市） |
| Kiki，帮我打开 QQ | 打开应用 |
| Kiki，搜索 Purpur 配置 | 网页搜索 |
| Kiki，启动服务器 | 启动 Minecraft 服务器 |
| Kiki，关闭服务器 | 停止 Minecraft 服务器 |
| Kiki，服务器状态 | 检查服务器是否在线 |
| Kiki，服务器执行 say 大家好 | 发送 RCON 控制台指令 |
| Kiki，帮我压缩桌面的文件夹 | 未知 → AI 生成 → 人工审核 |

---

## 🔄 工作流程图

```
麦克风持续录音
      │
      ▼
┌─────────────┐
│  Porcupine  │  ← 检测到 "Kiki" 唤醒词
│  唤醒词检测  │
└──────┬──────┘
       │  触发
       ▼
┌─────────────┐
│Faster-Whisper│ ← 录制并识别语音
│  语音识别   │
└──────┬──────┘
       │  文本
       ▼
┌─────────────┐
│  Ollama     │ ← 本地 Qwen3:4B 模型
│ 意图解析    │ ← 输出标准 JSON
└──────┬──────┘
       │  {"intent":"...", "target":"..."}
       ▼
┌─────────────┐
│  命令路由器  │ ← 根据 intent 分发
└──────┬──────┘
       │
  ┌────┴──────────────────────────┐
  │                               │
  ▼                               ▼
已知意图                        未知意图
  │                               │
  ├─ weather.py                   ▼
  ├─ open_app.py          Ollama 生成代码
  ├─ search_web.py                │
  ├─ minecraft.py         弹窗人工审核
  └─ 直接执行                     │
                           通过 → 保存技能
                           拒绝 → 丢弃
```

---

## ⚠️ 安全说明

- **自学习技能必须经过人工审核**，Kiki 绝对不会自动执行 AI 生成的代码
- 审核窗口会显示完整代码，请检查是否存在危险操作（删除文件、格式化磁盘等）
- 所有处理均在**本地**完成，语音和指令数据不会上传至任何服务器
- Porcupine 唤醒词检测也是**完全本地**运行

---

## 🔧 自定义唤醒词

默认使用 Porcupine 内置关键词（仅供测试），正式使用请训练自定义 "Kiki" 唤醒词：

1. 登录 [https://console.picovoice.ai/](https://console.picovoice.ai/)
2. 进入 **Porcupine** → **Train a custom model**
3. 输入唤醒词 `Kiki`，选择 Windows 平台，下载 `.ppn` 文件
4. 将 `.ppn` 文件放入 `config/kiki_windows.ppn`

---

## 📦 添加新技能

1. 在 `skills/` 目录新建 `your_skill.py`，实现 `handle(intent: dict)` 函数：

```python
def handle(intent: dict):
    target = intent.get("target", "")
    # 你的逻辑
    print(f"[Kiki] 执行了 {target}")
```

2. 在 `core/intent_parser.py` 的 `SYSTEM_PROMPT` 中添加新的意图名称

3. 在 `core/command_router.py` 的 `INTENT_MAP` 中注册：

```python
from skills import your_skill

INTENT_MAP = {
    ...
    "your_intent": your_skill.handle,
}
```

---

## 🛠️ 常见问题

**Q: 启动报错 `No module named 'pyaudio'`**  
A: 运行 `pipwin install pyaudio`

**Q: Whisper 加载很慢**  
A: 第一次会下载模型文件（约 500MB），之后会缓存，正常启动很快

**Q: Ollama 连接失败**  
A: 确认已运行 `ollama serve`，且端口 11434 没有被防火墙拦截

**Q: Porcupine 报错 `Invalid access key`**  
A: 检查环境变量 `PORCUPINE_ACCESS_KEY` 是否正确设置

**Q: Minecraft 服务器无法通过 RCON 控制**  
A: 检查 `server.properties` 中 `enable-rcon=true`，以及 `.env` 中密码是否一致

---

## 🗺️ 开发路线图

- [x] 唤醒词检测
- [x] 语音识别（Faster-Whisper）
- [x] AI 意图解析（Ollama + Qwen3）
- [x] 天气查询
- [x] 打开应用
- [x] 网页搜索
- [x] Minecraft 服务器控制（含 RCON）
- [x] 未知指令 → AI 生成 → 人工审核 → 保存技能
- [ ] TTS 语音回复（pyttsx3 / Edge-TTS）
- [ ] 已学习技能的自动路由（不经过 AI 直接执行）
- [ ] 图形化配置界面
- [ ] 多语言唤醒词支持

---

## 📄 License

MIT License — 自由使用、修改、分发。

---

## 🙏 致谢

- [Picovoice Porcupine](https://github.com/Picovoice/porcupine) — 唤醒词检测
- [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) — 高速语音识别
- [Ollama](https://ollama.com/) — 本地大模型运行
- [Qwen3](https://github.com/QwenLM/Qwen3) — 阿里巴巴开源中文大模型
- [wttr.in](https://github.com/chubin/wttr.in) — 免费天气接口
