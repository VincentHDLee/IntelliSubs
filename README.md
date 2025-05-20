# 智字幕 (IntelliSubs) - AI驱动的字幕生成工具 (日语市场版)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) <!-- Placeholder, update if different license -->

智字幕 (IntelliSubs) 是一款专为新媒体内容创作者（特别是针对日本市场）设计的桌面应用软件。它利用先进的AI技术（ASR和可选的LLM）自动化或半自动化地为日语视频/音频内容生成高质量的SRT、LRC、ASS等格式字幕，旨在显著提升字幕制作效率，降低人工成本。

## 主要功能

*   **精准日语语音识别：** 基于优化的ASR引擎（如OpenAI Whisper），针对标准AI生成的日语人声音轨进行高效转写。
*   **多格式字幕导出：** 支持主流的SRT、LRC、ASS字幕格式。
*   **文本智能优化 (可选)：**
    *   日语标点符号自动补全与规范化。
    *   通过自定义词典修正特定术语、品牌名。
    *   集成LLM进行文本润色、语法修正。
*   **灵活的输入方式：** 支持纯音频文件 (MP3, WAV, M4A) 和包含音轨的视频文件 (MP4, MOV)。
*   **用户友好界面：** 简洁直观的桌面应用界面 (Windows优先)，易于上手。
*   **可配置选项：** 用户可选择ASR模型大小、CPU/GPU处理模式、是否启用LLM增强等。

## 安装指南 (Windows)

*详细安装步骤将在后续版本中提供。初步设想为提供可直接运行的 `.exe` 程序或解压缩即用的文件夹。*

1.  从发布页面下载最新的 `IntelliSubs-vx.x.x-setup.exe` 安装包或 `IntelliSubs-vx.x.x-portable.zip` 压缩包。
2.  **安装版：** 运行安装程序，按照提示完成安装。
3.  **便携版：** 将ZIP文件解压缩到您选择的任意文件夹。
4.  运行 `IntelliSubs.exe` 启动应用程序。

## 快速上手

1.  启动智字幕 (IntelliSubs) 应用程序。
2.  点击“选择文件”按钮，选择您的日语MP3/WAV音频文件或MP4/MOV视频文件。
3.  (可选) 根据需要调整ASR模型大小、处理设备(CPU/GPU)等设置。
4.  点击“开始生成”按钮。
5.  等待处理完成，生成的字幕文本将显示在预览区域。
6.  选择您需要的导出格式 (SRT, LRC, ASS)。
7.  点击“导出字幕”按钮，选择保存位置。

## 获取帮助与反馈

*   如果您在使用过程中遇到任何问题，请查阅 [`docs/troubleshooting.md`](docs/troubleshooting.md) (待创建)。
*   欢迎通过项目的 [GitHub Issues](https://github.com/VincentHDLee/IntelliSubs/issues) 页面报告BUG或提出功能建议。

## 详细文档

*   **用户手册:** [`docs/user_manual/index.md`](docs/user_manual/index.md) (待创建)
*   **开发者指南:** [`docs/developer_guide/index.md`](docs/developer_guide/index.md) (待创建)
*   **项目规划与设计:** [`DEVELOPMENT.md`](DEVELOPMENT.md)
*   **项目结构:** [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md)
*   **文档结构:** [`DOCUMENTATION_STRUCTURE.md`](DOCUMENTATION_STRUCTURE.md)

## 贡献

我们欢迎各种形式的贡献！请查阅 [`CONTRIBUTING.md`](CONTRIBUTING.md) (待创建) 了解详情。

## 许可证

本项目采用 [MIT License](LICENSE) (待创建)授权。