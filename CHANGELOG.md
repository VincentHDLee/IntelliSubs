# 更新日志

所有此项目的 উল্লেখযোগ্য更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且此项目遵循 [Semantic Versioning](https://semver.org/spec/v2.0.0.html)。

## [0.1.0] - 2025-05-21

### 新增

- **核心功能:**
    - 实现基本的音频/视频文件处理流程。
    - 集成 `faster-whisper` 进行日语 ASR 转录。
    - 实现文本规范化、标点符号添加和字幕分段。
    - 支持将字幕导出为 SRT, LRC, ASS, 和 TXT 格式。
- **用户界面 (UI):**
    - 创建了基于 `customtkinter` 的基本用户界面。
    - UI 包含文件选择、处理选项（ASR 模型、设备）、字幕预览和导出功能。
- **配置管理:**
    - 实现加载和保存应用程序配置（例如 ASR 模型、设备选择）。
- **日志记录:**
    - 在整个应用程序中集成了日志记录功能。
- **项目结构与文档:**
    - 建立了初始项目结构。
    - 添加了 `README.md`, `DEVELOPMENT.md`, `PROJECT_STRUCTURE.md` 等基础文档。
- **依赖管理:**
    - 创建了 `requirements.txt` 用于管理 Python 依赖。

### 修复

- 修正了多个模块中的日志记录问题，统一使用 `logging` 模块。
- 解决了 Python 模块导入路径问题，确保应用程序可以正确启动。
- 修复了在处理配置文件时 `ConfigManager` 的错误。
- 修复了 `faster-whisper` 调用中的参数错误。
- 修复了 UI 中因 `os` 模块未导入而导致的 `NameError`。