# Seedance Video Toolkit

基于豆包 Seedream / Seedance 模型的 AI 视频生成工具。包含 GUI 和 CLI 两种模式。

## GUI 模式

桌面应用，输入项目描述，自动规划场景、生成参考图、生成视频片段，一键出片。

### 功能

- **项目管理** — 创建/编辑/删除视频项目，向导式 4 步建项流程
- **LLM 场景规划** — 调用智谱 AI GLM 自动生成中英文场景描述 + 提示词
- **AI 生图** — 调用豆包 Seedream 3.0 生成场景参考图
- **AI 生视频** — 调用豆包 Seedance 1.0 Pro 生成场景视频片段（图生视频）
- **实时预览** — 图片/视频画廊即时预览，视频悬停播放
- **剪映集成** — 自动生成剪映编辑指令
- **API 密钥管理** — GUI 内配置，密钥本地加密存储，不硬编码

### 运行

```bash
python main.py
```

或双击 `run.bat`（Windows）。

## CLI 模式

通用独立 CLI 工具，用于从文档生成演示视频的完整工作流：

1. **init** — 创建项目目录结构
2. **plan** — 从源文档生成项目计划 (`project_job.json`)
3. **slides** — 生成 LaTeX Beamer 幻灯片并编译为 PDF
4. **video** — 编排文生图 / 图生视频任务，生成媒体文件
5. **jianying** — 直接通过 JyProject API 生成剪映 Pro 草稿
6. **full** — 一键执行以上全流程
7. **setup** — 交互式配置向导

不需要 Claude Code 或任何外部 AI 助手。

## 环境要求

- **Python 3.10+**
- **MiKTeX** (含 XeLaTeX) — 用于编译 LaTeX 幻灯片
- **Node.js 18+** — 用于辅助验证脚本
- **剪映 Pro 5.9.0** (JianYing) — 用于视频编辑（[锁定版本说明](https://www.zhihu.com/question/1933842682532308089) | [下载](https://xu5.cc/)）
- **Git** — 用于 submodule 管理

## 快速开始

### 安装

```bash
git clone https://github.com/phanghonghao/GUI-seedance-video-toolkit.git
cd GUI-seedance-video-toolkit
pip install -r requirements.txt
```

或使用 CLI 一键安装：

```powershell
setup.bat
```

`setup.bat` 会自动：
- 初始化 `libs/jianying-editor` git submodule
- 安装 Python 依赖
- 启动交互式配置向导

### 配置 API 密钥

GUI 模式：运行程序后在 **API 配置** 页面填入密钥并测试连接。

CLI 模式：运行交互式向导 `python video-full.py setup`，或手动编辑配置文件。

| 提供商 | 用途 | 注册/文档 |
|--------|------|----------|
| **智谱 AI** (Zhipu) | LLM 场景规划 | 清华同学：[EasyCompute](https://easycompute.cs.tsinghua.edu.cn/home)（右上角 GLM 套餐） |
| **并行科技** (Paratera) | 豆包生图/生视频 | [使用文档](https://ai.paratera.com/document/llm/support/lmsOffline) / [API 平台](https://llmapi.paratera.com) |

### CLI 验证

```powershell
python video-full.py config
```

### 打包为 EXE

```bash
python setup.py
# 输出: release/VideoGeneratorPro.exe
```

## CLI 命令参考

```powershell
python video-full.py setup     # 交互式配置向导
python video-full.py config    # 验证运行环境
python video-full.py init --project demo
python video-full.py plan --project demo --source C:\docs
python video-full.py slides --config C:\path\project_job.json
python video-full.py video --config C:\path\project_job.json --dry-run
python video-full.py jianying --config C:\path\project_job.json
python video-full.py full --project demo --source C:\docs
```

## 配置文件

| 文件 | 用途 |
|------|------|
| `config/providers.json` | 图片/视频 API 配置 |
| `config/jianying.json` | 剪映草稿路径、分辨率、语音等 |
| `config/miktex.json` | XeLaTeX 编译配置 |
| `config/nodejs.json` | Node.js 命令路径 |
| `config/project-defaults.json` | 项目默认参数 |
| `.env` | API key 等敏感信息（不纳入 Git） |

## 项目结构

```
GUI-seedance-video-toolkit/
├── main.py                      # GUI 入口
├── cli.py                       # CLI 入口 + env_loader
├── video-full.py                # CLI 启动器
├── api_client.py                # API 客户端（智谱/并行科技）
├── commands/                    # CLI 各子命令实现
│   ├── setup.py                 # 交互式配置向导
│   ├── config.py                # 环境检查
│   ├── init.py / plan.py / slides.py / video.py / jianying.py / full.py
├── core/
│   ├── env_loader.py            # .env 解析（纯 stdlib）
│   ├── jianying_automation.py   # 直接调用 JyProject API
│   ├── jianying_pipeline.py     # 剪映工作流编排
│   ├── app.py                   # QApplication 初始化 (GUI)
│   └── theme.py                 # UI 主题 (GUI)
├── viewmodels/                  # ViewModel 层 (GUI)
├── views/                       # UI 层 (GUI)
├── libs/
│   └── jianying-editor/         # git submodule — JyProject 封装
├── config/                      # JSON 配置文件
├── tests/                       # API 连通性测试
├── setup.bat                    # 一键安装脚本
└── requirements.txt             # Python 依赖
```

## 许可证

MIT License
