# 智字幕 (IntelliSubs) - AI驱动的多语言字幕生成工具

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

智字幕 (IntelliSubs) 是一款专为全球新媒体内容创作者设计的桌面应用软件。它利用先进的AI技术（ASR和可选的LLM）自动化或半自动化地为多种语言（包括中文、英文、日文等）的视频/音频内容生成高质量的SRT、LRC、ASS等格式字幕，旨在显著提升字幕制作效率，降低人工成本。

## 主要功能

*   **精准多语言语音识别：** 基于优化的ASR引擎（如 faster-whisper），支持对中文、英文、日文及更多ASR支持的语言的人声音轨进行高效转写。
*   **多文件批量处理**: 支持一次选择和处理多个音视频文件，可统一指定输出目录。
*   **智能时间轴调整**: 自动优化字幕的最小显示时长和字幕间的间隔，提升观看体验（参数可在高级设置中调整）。
*   **多格式字幕导出：** 支持主流的SRT、LRC、ASS、TXT字幕格式。
*   **文本智能优化 (可选)：**
    *   多语言标点符号自动补全与规范化。
    *   通过自定义词典修正特定术语、品牌名。
    *   集成LLM进行文本润色、语法修正 (需用户配置API)。系统会向LLM发送优化指令，并内置响应解析逻辑，以尽可能提取纯净的优化后字幕文本。
*   **灵活的输入方式：** 支持纯音频文件 (MP3, WAV, M4A) 和包含音轨的视频文件 (MP4, MOV, MKV)。
*   **用户友好界面**: 采用标签页布局，清晰区分主要操作设置与AI及高级微调选项。
*   **可配置选项：** 用户可选择ASR模型大小、CPU/GPU处理模式、是否启用LLM增强、配置LLM参数、自定义词典、处理语言以及时间轴调整参数等。

## 安装与运行

建议在 Python 虚拟环境中运行本项目以管理依赖。

1.  **克隆仓库** (如果您尚未操作):
    ```bash
    git clone https://github.com/VincentHDLee/IntelliSubs.git
    cd IntelliSubs
    ```
2.  **创建并激活虚拟环境**:
    *   使用 `venv` (Python 内置):
        ```bash
        python -m venv venv
        # Windows
        .\venv\Scripts\activate
        # macOS/Linux
        source venv/bin/activate
        ```
    *   或者使用 `conda` (推荐 Python 3.9 或更高版本):
        ```bash
        conda create -n intellisubs_env python=3.9
        conda activate intellisubs_env
        ```
3.  **安装依赖**:
    在激活的虚拟环境中，运行：
    ```bash
    pip install -r requirements.txt
    ```
4.  **运行程序**:
    *   在 Windows 上，您可以直接运行根目录下的 `run_intellisubs.bat` 批处理文件。
    *   或者，通过 Python 解释器运行主程序：
        ```bash
        python intellisubs/main.py
        ```

## 快速上手

1.  按照上述“安装与运行”指南启动 智字幕 (IntelliSubs) 应用程序。
2.  在主界面，点击“选择文件(可多选)”按钮，选择一个或多个音频/视频文件（支持中文、英文、日文等多种语言）。已选文件将显示在“已选文件列表”中。
3.  (可选) 点击“选择目录”按钮设置“输出目录”，否则导出的字幕将提示单独保存或按默认规则处理。
4.  在“主要设置”标签页中：
    *   根据需要调整“ASR模型”（如 `base`, `small`, `medium` 等）和“处理设备”（CPU/GPU）。
    *   (可选) 若有针对特定语言的“自定义词典”，点击“浏览...”选择词典文件 (CSV/TXT格式)。
    *   在“处理语言”下拉菜单中选择您媒体文件对应的语言。
5.  (可选) 切换到“AI 及高级设置”标签页：
    *   若需使用LLM增强，勾选“启用LLM增强”，并填写您的“LLM API Key”、“LLM Base URL (可选)”及“LLM 模型名称”。
    *   调整“智能时间轴调整”的“最小显示时长 (秒)”和“最小间隔时长 (秒)”参数。
6.  点击主界面顶部的“开始生成字幕”按钮。
7.  处理过程和结果会显示在下方的“处理结果”区域。对于成功处理的文件，可以点击其对应的“预览”按钮，在主“字幕预览”框中查看生成的字幕内容。
8.  在“字幕预览”框下方，从下拉菜单中选择所需的导出格式 (SRT, LRC, ASS, TXT)。
9.  点击“导出当前预览”按钮，选择保存位置以保存当前预览的字幕文件。
10. 若已设置有效的“输出目录”，且有多个文件成功处理，可点击“导出所有成功”按钮，将所有成功生成的字幕按选定格式批量导出到指定输出目录。

## 获取帮助与反馈

*   如果您在使用过程中遇到任何问题，请查阅 [`docs/troubleshooting.md`](docs/troubleshooting.md:1)。
*   欢迎通过项目的 [GitHub Issues](https://github.com/VincentHDLee/IntelliSubs/issues) 页面报告BUG或提出功能建议。

## 详细文档

*   **项目文档首页:** [`docs/index.md`](docs/index.md:1)
*   **用户手册:**
    *   用户手册首页: [`docs/user_manual/index.md`](docs/user_manual/index.md:1)
    *   安装指南: [`docs/user_manual/installation.md`](docs/user_manual/installation.md:1)
    *   快速入门: [`docs/user_manual/quick_start.md`](docs/user_manual/quick_start.md:1)
    *   常见问题: [`docs/user_manual/faq.md`](docs/user_manual/faq.md:1)
    *   功能详解:
        *   输入与输出: [`docs/user_manual/features/input_output.md`](docs/user_manual/features/input_output.md:1)
        *   ASR 设置: [`docs/user_manual/features/asr_settings.md`](docs/user_manual/features/asr_settings.md:1)
        *   LLM 增强: [`docs/user_manual/features/llm_enhancement.md`](docs/user_manual/features/llm_enhancement.md:1)
        *   自定义词典: [`docs/user_manual/features/custom_dictionary.md`](docs/user_manual/features/custom_dictionary.md:1)
        *   字幕预览: [`docs/user_manual/features/preview.md`](docs/user_manual/features/preview.md:1)
        *   字幕导出: [`docs/user_manual/features/subtitle_export.md`](docs/user_manual/features/subtitle_export.md:1)
*   **开发者指南:**
    *   开发者指南首页: [`docs/developer_guide/index.md`](docs/developer_guide/index.md:1)
    *   环境设置: [`docs/developer_guide/setup_env.md`](docs/developer_guide/setup_env.md:1)
    *   编码规范: [`docs/developer_guide/coding_standards.md`](docs/developer_guide/coding_standards.md:1)
    *   构建与打包: [`docs/developer_guide/build_and_packaging.md`](docs/developer_guide/build_and_packaging.md:1)
    *   架构概览: [`docs/developer_guide/architecture/overview.md`](docs/developer_guide/architecture/overview.md:1)
    *   具体指南:
        *   添加新的ASR引擎: [`docs/developer_guide/guides/adding_new_asr_engine.md`](docs/developer_guide/guides/adding_new_asr_engine.md:1)
        *   扩展字幕格式: [`docs/developer_guide/guides/extending_subtitle_formats.md`](docs/developer_guide/guides/extending_subtitle_formats.md:1)
        *   修改UI: [`docs/developer_guide/guides/modifying_the_ui.md`](docs/developer_guide/guides/modifying_the_ui.md:1)
*   **项目变更日志:** [`CHANGELOG.md`](CHANGELOG.md:1)
*   **项目规划与设计:** [`DEVELOPMENT.md`](DEVELOPMENT.md:1)
*   **项目结构:** [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md:1)
*   **文档结构:** [`DOCUMENTATION_STRUCTURE.md`](DOCUMENTATION_STRUCTURE.md:1)

## 贡献

我们欢迎各种形式的贡献！请查阅 [`CONTRIBUTING.md`](CONTRIBUTING.md:1) 了解详情。

## 许可证

本项目采用 [MIT License](LICENSE) 授权。