# video-generator-full-cli

通用独立 CLI 工具，用于从文档生成演示视频的完整工作流：

1. **init** — 创建项目目录结构
2. **plan** — 从源文档生成项目计划 (`project_job.json`)
3. **slides** — 生成 LaTeX Beamer 幻灯片并编译为 PDF
4. **video** — 编排文生图 / 图生视频任务，生成媒体文件
5. **jianying** — 直接通过 JyProject API 生成剪映 Pro 草稿
6. **full** — 一键执行以上全流程

不需要 Claude Code 或任何外部 AI 助手。

## 前置条件

- **Python 3.10+**
- **MiKTeX** (含 XeLaTeX) — 用于编译 LaTeX 幻灯片
- **Node.js 18+** — 用于辅助验证脚本
- **剪映 Pro 5.9.0** (JianYing) — 用于视频编辑（[锁定版本说明](https://www.zhihu.com/question/1933842682532308089) | [下载](https://xu5.cc/)）
- **Git** — 用于 submodule 管理

## 快速开始

### 1. Clone & 安装依赖

```powershell
git clone <repo-url>
cd video-generator-full-cli
setup.bat
```

`setup.bat` 会自动：
- 初始化 `libs/jianying-editor` git submodule
- 安装 Python 依赖 (`pip install -r requirements.txt`)
- 启动交互式配置向导

### 2. 手动安装（替代方案）

```powershell
git submodule update --init --recursive
pip install -r requirements.txt
python video-full.py setup
```

### 3. 配置

运行交互式向导：

```powershell
python video-full.py setup
```

向导会自动检测：
- 剪映 Pro 草稿路径 (`%LOCALAPPDATA%\JianyingPro\...`)
- MiKTeX / XeLaTeX 位置
- Node.js 位置
- API key 和 base URL

也可手动编辑配置文件或设置环境变量（见 `.env.example`）。

### 4. 验证

```powershell
python video-full.py config
```

## 命令参考

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

## 架构

```
video-generator-full-cli/
├── cli.py                  # CLI 入口 + env_loader
├── commands/               # 各子命令实现
│   ├── setup.py            # 交互式配置向导
│   ├── config.py           # 环境检查
│   ├── init.py / plan.py / slides.py / video.py / jianying.py / full.py
├── core/
│   ├── env_loader.py       # .env 解析（纯 stdlib）
│   ├── jianying_automation.py  # 直接调用 JyProject API
│   ├── jianying_pipeline.py    # 剪映工作流编排
│   └── ...
├── libs/
│   └── jianying-editor/    # git submodule — JyProject 封装
├── config/                 # JSON 配置文件
├── setup.bat               # 一键安装脚本
└── requirements.txt        # Python 依赖
```

### 剪映自动化

剪映草稿通过 `libs/jianying-editor` submodule 的 JyProject Python API 直接生成，无需 Claude Code。

工作流：
1. `core/jianying_pipeline.py` 读取 `media_manifest.json` 和 `jianying.json` 配置
2. `core/jianying_automation.py` 调用 `JyProject` 创建剪映草稿
3. 媒体文件按时间线顺序导入，可选添加字幕
4. 项目保存到剪映草稿目录，打开剪映 Pro 即可看到

## 环境变量

参考 `.env.example`。支持的环境变量：

- `VIDEO_FULL_IMAGE_API_KEY` / `VIDEO_FULL_IMAGE_API_BASE`
- `VIDEO_FULL_VIDEO_API_KEY` / `VIDEO_FULL_VIDEO_TASK_URL` / `VIDEO_FULL_VIDEO_STATUS_URL`
- `VIDEO_FULL_XELATEX_COMMAND`
