# 更新日志

所有此项目的更新更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且此项目遵循 [Semantic Versioning](https://semver.org/spec/v2.0.0.html)。

## [0.1.3] - 2025-05-26

### 新增

- **UI 功能**:
    - 在字幕预览区域 ([`intellisubs/ui/views/main_window_components/results_panel.py`](intellisubs/ui/views/main_window_components/results_panel.py:1))实现了字幕时间码和文本的逐行编辑功能：
        - 将原有的整块文本预览框替换为可滚动的字幕条目列表。
        - 每个字幕条目显示序号、开始时间、结束时间和字幕文本，均在 `CTkEntry` 中显示和编辑。
        - 用户修改后，可通过“应用更改”按钮验证输入（时间格式、逻辑顺序）并将更改更新到内存中的字幕数据。
        - 增加了对 `pysrt` 模块的依赖以处理时间对象的解析和格式化。
    - 在逐行字幕编辑器中添加了**删除行**和**插入新行**（在末尾）的基本操作 ([`intellisubs/ui/views/main_window_components/results_panel.py`](intellisubs/ui/views/main_window_components/results_panel.py:1))。

### 文档

- 在 [`DEVELOPMENT.md`](DEVELOPMENT.md:1) 中将“字幕时间码精确调整 (D2I0)”任务状态从“[D2I0 - 完成待测试]”更新为“[TODO D2I0]”，遵循用户指示跳过测试阶段。
- 在 [`DEVELOPMENT.md`](DEVELOPMENT.md:1) 中将“基本字幕操作 (D2I1)”（已实现插入、删除）任务状态从“[D2I1 - 完成待测试]”更新为“[TODO D2I1]”，遵循用户指示跳过测试阶段。

### 改进

- **开发流程**:
    - 在 [`DEVELOPMENT.md`](DEVELOPMENT.md:1) 中将“基本字幕操作 (D2I1)”任务标记为进行中。

### 修复

- 解决了在 `MainWindow` 的 `handle_file_selection_update` 方法中调用 `ResultsPanel.set_main_preview_content` 时因参数数量不匹配而导致的 `TypeError` ([`intellisubs/ui/views/main_window.py:88`](intellisubs/ui/views/main_window.py:88))。调整了调用以匹配更新后的方法签名，确保在选择文件后正确重置字幕编辑/预览区域。
- 解决了在 `ResultsPanel.set_main_preview_content` 中当 `file_path` 为 `None` 时调用 `os.path.basename` 导致的 `TypeError` ([`intellisubs/ui/views/main_window_components/results_panel.py:168`](intellisubs/ui/views/main_window_components/results_panel.py:168))。
- 解决了在 `MainWindow._run_processing_in_thread` 中调用 `ResultsPanel.set_main_preview_content` 时因参数数量不匹配而导致的 `TypeError` ([`intellisubs/ui/views/main_window.py:278`](intellisubs/ui/views/main_window.py:278))。
- **核心数据流重构与修复**:
    - 在 `WorkflowManager` ([`intellisubs/core/workflow_manager.py:331`](intellisubs/core/workflow_manager.py:331)) 中，将字幕分段器输出的字典列表统一转换为 `pysrt.SubRipItem` 对象列表。
    - 更新了所有字幕格式化程序 (`SRTFormatter` ([`intellisubs/core/subtitle_formats/srt_formatter.py:1`](intellisubs/core/subtitle_formats/srt_formatter.py:1)), `LRCFormatter` ([`intellisubs/core/subtitle_formats/lrc_formatter.py:1`](intellisubs/core/subtitle_formats/lrc_formatter.py:1)), `ASSFormatter` ([`intellisubs/core/subtitle_formats/ass_formatter.py:1`](intellisubs/core/subtitle_formats/ass_formatter.py:1)), `TxtFormatter` ([`intellisubs/core/subtitle_formats/txt_formatter.py:1`](intellisubs/core/subtitle_formats/txt_formatter.py:1))) 以正确处理 `List[pysrt.SubRipItem]` 作为输入，解决了在 `SRTFormatter` ([`intellisubs/core/subtitle_formats/srt_formatter.py:57`](intellisubs/core/subtitle_formats/srt_formatter.py:57)) 中发生的 `TypeError: argument of type 'SubRipItem' is not iterable`。
    - `SRTFormatter.parse_srt_string` ([`intellisubs/core/subtitle_formats/srt_formatter.py:72`](intellisubs/core/subtitle_formats/srt_formatter.py:72)) 也更新为使用 `pysrt` 库进行解析并返回 `List[pysrt.SubRipItem]`。
    - 移除了 `SRTFormatter` ([`intellisubs/core/subtitle_formats/srt_formatter.py:1`](intellisubs/core/subtitle_formats/srt_formatter.py:1)) 和 `LRCFormatter` ([`intellisubs/core/subtitle_formats/lrc_formatter.py:1`](intellisubs/core/subtitle_formats/lrc_formatter.py:1)) 中因 `pysrt` 的引入而变得多余的时间格式化辅助函数。
- 解决了在 `MainWindow.export_all_successful_subtitles_from_results_panel` 中调用 `ResultsPanel.update_export_buttons_state` 时因参数不匹配而导致的 `TypeError` ([`intellisubs/ui/views/main_window.py:475`](intellisubs/ui/views/main_window.py:475))。

## [0.1.2] - 2025-05-26

### 文档

- 更新了 [`DEVELOPMENT.md`](DEVELOPMENT.md:1) 中字幕编辑功能的任务状态，将“字幕文本直接编辑”从未测试（待测试）标记为待办（TODO）。

### 改进

- **开发流程**:
    - 在 [`DEVELOPMENT.md`](DEVELOPMENT.md:1) 中将“字幕时间码精确调整 (D2I0)”任务标记为进行中。

## [0.1.1] - 2025-05-23

### 新增

- **核心功能**:
    - 在字幕分段器 (`SubtitleSegmenter`) 中引入了智能时间轴调整功能，通过新的 `min_duration_sec` 和 `min_gap_sec` 参数，实现对字幕最小显示时长和字幕间最小间隔的自动调整，以优化观看体验。

### 改进

- **开发流程**:
    - 暂时注释掉了 GitHub Actions workflow ([`.github/workflows/python-tests.yml`](.github/workflows/python-tests.yml:1)) 中的自动触发条件，以方便当前阶段的开发和测试。

### 重构

- **UI 架构**:
    - 重构 `intellisubs/ui/views/main_window.py` ([`intellisubs/ui/views/main_window.py`](intellisubs/ui/views/main_window.py:1))，将其功能拆分到新的子面板模块中：
        - `intellisubs/ui/views/main_window_components/top_controls_panel.py` ([`intellisubs/ui/views/main_window_components/top_controls_panel.py`](intellisubs/ui/views/main_window_components/top_controls_panel.py:0))
        - `intellisubs/ui/views/main_window_components/settings_panel.py` ([`intellisubs/ui/views/main_window_components/settings_panel.py`](intellisubs/ui/views/main_window_components/settings_panel.py:0))
        - `intellisubs/ui/views/main_window_components/results_panel.py` ([`intellisubs/ui/views/main_window_components/results_panel.py`](intellisubs/ui/views/main_window_components/results_panel.py:0))
    - `MainWindow` 现在主要作为这些UI组件的协调器，其代码行数从900多行减少到约538行，提高了代码的可读性、可维护性。

### 文档

- 更新了用户手册的快速入门指南 ([`docs/user_manual/quick_start.md`](docs/user_manual/quick_start.md:1))，在“主要功能”部分增加了对“智能时间轴调整”功能的初步提及。
- 更新了UI架构设计文档 ([`docs/developer_guide/architecture/ui_design.md`](docs/developer_guide/architecture/ui_design.md:1))，以反映 `MainWindow` 的重构和新子面板的引入。
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
    - **多文件处理界面**:
        - 实现多文件选择功能，允许用户一次选择并处理多个音视频文件。
        - 增加“已选文件列表”区域，显示用户选择的所有文件名。
        - 提供“选择输出目录”功能，允许用户指定所有字幕文件的保存位置。
        - 新增“处理结果”列表，动态显示每个文件的处理状态（成功/失败）和错误信息（如果处理失败）。
        - 结果列表中的成功条目包含“预览”按钮，点击可将对应字幕加载到主“字幕预览”区域。
        - 新增“导出所有成功字幕”按钮，可将所有成功处理的字幕文件按选定格式批量导出到指定输出目录。
- **配置管理:**
    - 实现加载和保存应用程序配置（例如 ASR 模型、设备选择）。
- **日志记录:**
    - 在整个应用程序中集成了日志记录功能。
- **项目结构与文档:**
    - 建立了初始项目结构。
    - 添加了 `README.md`, `DEVELOPMENT.md`, `PROJECT_STRUCTURE.md` 等基础文档。
- **依赖管理:**
    - 创建了 `requirements.txt` 用于管理 Python 依赖。

### 改进

- **LLM 交互**:
    - 重构 LLM 增强模块 (`LLMEnhancer`) 以使用直接 HTTP 请求 (`httpx`)，取代了之前的 OpenAI SDK 调用，旨在提高对各类兼容 OpenAI API 的中转服务的兼容性。
    - 实现了更灵活的 LLM 服务基础 URL (Base URL) 处理逻辑，允许用户仅配置服务域名。
    - 增强了 LLM API 请求和响应的日志记录，包括完整的响应体（debug级别）以方便问题排查。
    - 优化了 LLM 的 prompt 设计，使其更具体并包含示例，调整了 `temperature` 和 `max_tokens` 等请求参数，尝试提升输出质量。
    - 加强了 LLM 处理过程中的错误处理和回退机制，确保在LLM调用失败或返回无效内容时程序能平稳降级。
- **日志安全**:
    - 在应用程序日志中实现了对敏感数据（如 API 密钥）的自动遮蔽功能，以增强安全性。
- **资源管理**:
    - 为 LLM 模块使用的 HTTP 客户端添加了资源清理逻辑，确保在应用程序退出时能正确关闭连接。

### 修复

- 修正了多个模块中的日志记录问题，统一使用 `logging` 模块。
- 解决了 Python 模块导入路径问题，确保应用程序可以正确启动。
- 修复了在处理配置文件时 `ConfigManager` 的错误。
- 修复了 `faster-whisper` 调用中的参数错误。
- 修复了 UI 中因 `os` 模块未导入而导致的 `NameError`。

### 已知问题

- **LLM 增强效果**:
    - 当前配置下（模型 `gemini-2.5-flash-preview-04-17`，通过 `https://sucoiapi.com` 中转服务），LLM 字幕增强功能在实际调用时，API 服务端返回的优化后文本内容为空字符串。
    - 尽管程序已尝试多种兼容性调整（包括直接HTTP调用、优化Prompt、调整参数），此问题依旧存在。应用程序在这种情况下会回退到使用未经LLM优化的ASR原始文本。
    - 此问题可能与所选中转服务对特定模型的支持程度、模型本身对当前优化任务的适应性，或需要更特殊的API调用参数/格式有关。暂停进一步的LLM交互模块开发，等待更多关于该中转API行为或模型兼容性的信息。