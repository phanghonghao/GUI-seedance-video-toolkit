# Seedance Video Toolkit (GUI)

基于豆包 Seedream / Seedance 模型的 AI 视频生成桌面工具。输入项目描述，自动规划场景、生成参考图、生成视频片段，一键出片。

## 功能

- **项目管理** — 创建/编辑/删除视频项目，向导式 4 步建项流程
- **LLM 场景规划** — 调用智谱 AI GLM 自动生成中英文场景描述 + 提示词
- **AI 生图** — 调用豆包 Seedream 3.0 生成场景参考图
- **AI 生视频** — 调用豆包 Seedance 1.0 Pro 生成场景视频片段（图生视频）
- **实时预览** — 图片/视频画廊即时预览，视频悬停播放
- **剪映集成** — 自动生成剪映编辑指令
- **API 密钥管理** — GUI 内配置，密钥本地加密存储，不硬编码

## 快速开始

### 环境要求

- Python 3.10+
- Windows 10/11（macOS/Linux 也可运行，但未充分测试）

### 安装

```bash
git clone https://github.com/phanghonghao/GUI-seedance-video-toolkit.git
cd GUI-seedance-video-toolkit
pip install -r requirements.txt
```

### 配置 API 密钥

首次运行需要配置两个 API 密钥（在 GUI 内操作即可）：

| 提供商 | 用途 | 注册/文档 |
|--------|------|----------|
| **智谱 AI** (Zhipu) | LLM 场景规划 | 清华同学：[EasyCompute](https://easycompute.cs.tsinghua.edu.cn/home)（右上角 GLM 套餐） |
| **并行科技** (Paratera) | 豆包生图/生视频 | [使用文档](https://ai.paratera.com/document/llm/support/lmsOffline) / [API 平台](https://llmapi.paratera.com) |

运行程序后在 **API 配置** 页面填入密钥并测试连接。

### 运行

```bash
python main.py
```

或双击 `run.bat`（Windows）。

### 打包为 EXE

```bash
python setup.py
# 输出: release/VideoGeneratorPro.exe
```

## 使用流程

1. **新建项目** — 填写项目名称、描述、角色设定、视频风格
2. **场景规划** — 选择场景数量，LLM 自动生成或手动编辑
3. **开始生成** — 一键生成参考图 + 视频片段，实时进度跟踪
4. **查看结果** — 预览画廊查看图片/视频，点击按钮打开对应文件夹

## 项目结构

```
video-generator-gui/
├── main.py                      # 入口
├── api_client.py                # API 客户端（智谱/并行科技）
├── requirements.txt             # 依赖
├── setup.py                     # PyInstaller 打包
├── core/                        # 应用核心
│   ├── app.py                   # QApplication 初始化
│   └── theme.py                 # UI 主题 (QSS)
├── viewmodels/                  # ViewModel 层
│   ├── api_viewmodel.py         # API 配置逻辑
│   ├── generation_viewmodel.py  # 生成流程逻辑
│   └── project_viewmodel.py     # 项目管理逻辑
├── views/                       # UI 层
│   ├── main_window.py           # 主窗口
│   ├── wizards/                 # 向导对话框
│   │   ├── api_config_dialog.py
│   │   └── new_project_wizard.py
│   └── widgets/                 # 自定义组件
│       ├── image_gallery.py     # 媒体预览画廊
│       ├── progress_panel.py    # 进度面板
│       ├── project_card.py      # 项目卡片
│       └── styled_widgets.py    # 样式组件
├── tests/                       # API 连通性测试
└── cli_wrapper/                 # CLI 模块桥接
```

## 依赖

| 包 | 用途 |
|----|------|
| PyQt6 | GUI 框架 |
| openai | API 调用（OpenAI 兼容接口） |
| requests | HTTP 请求 |
| PyInstaller | 打包为 EXE（可选） |

## 测试 API 连通性

```bash
# 设置环境变量后运行测试
set ZHIPU_API_KEY=your-zhipu-key
set PARATERA_API_KEY=your-paratera-key

python tests/test_zhipu_llm.py
python tests/test_doubao_api.py
```

## 许可证

MIT License
