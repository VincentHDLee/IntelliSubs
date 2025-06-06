**项目文档：智字幕 (IntelliSubs) - AI驱动的字幕生成工具 (v1.1 - 全球市场版)**

**1. 项目背景与目标**

*   **背景：**
我司（新媒体公司）目前内容生产流程中，视频剪辑后的字幕制作环节仍存在较大的人力成本和时间开销。现有工作流涉及Gemini生成分镜脚本，文生图/图生视频模型产出素材，剪映进行剪辑。**业务覆盖全球市场，支持中文、英文、日文等多种语言。** 成品视频需要SRT、LRC、ASS等格式字幕。
*   **目标：**
开发一款名为“智字幕 (IntelliSubs)”的桌面应用软件（Windows平台优先），旨在自动化或半自动化地为成品视频（支持**中文、英文、日文等多种语言的AI生成的标准人声音轨**）生成高质量的字幕文件。软件将利用先进的ASR（自动语音识别）技术和可选的LLM（大语言模型）进行文本优化，以提高小编的工作效率，缩短内容生产周期。
*   **核心价值：**
*   显著降低多语言字幕制作的人工成本和时间。
    *   提升字幕的准确性和规范性。
    *   简化小编的工作流程。

**2. 目标用户**

*   公司内部负责多语言内容的新媒体小编、视频剪辑师。

**3. 核心功能需求**

*   **3.1. 输入模块**
    *   **主要输入：** 支持中、英、日等多种语言的人声音频文件（如MP3, WAV, M4A）。
    *   **辅助输入：** 包含支持语言音轨的短视频文件（如MP4, MOV），软件自动提取音轨。
    *   **(可选) 参考脚本：** 支持语言的文本文件（TXT, DOCX）。其主要用途是作为LLM优化时的上下文参考，帮助LLM理解专有名词或特定语境；次要用途是供用户对比查看ASR原始识别结果。程序不直接使用其进行强制校正。
    *   **输入/输出文件夹配置：**
        *   用户可以自定义输入文件夹（用于批量处理或选择源文件）和输出文件夹（用于存放生成的字幕文件）。
        *   若用户未设置，则默认输入文件夹为程序运行目录下的 `input` 文件夹，默认输出文件夹为程序运行目录下的 `output` 文件夹。这些默认文件夹将在程序首次尝试访问（如选择文件或执行转换任务）且文件夹不存在时自动创建。

*   **3.2. 音频预处理模块**
    *   **格式转换与标准化：** 自动将输入音频（如MP3）转换为ASR模型优化的格式（例如：16kHz采样率，单声道，16-bit WAV）。
    *   **(可选) 简单降噪：** 内置基础的降噪算法。鉴于音轨为AI生成标准语音，此功能优先级较低，主要应对意外情况。

*   **3.3. 语音识别 (ASR) 模块 (多语言支持)**
    *   **引擎选择：**
        *   **本地部署优先：**
            *   **OpenAI Whisper:** 通过 `faster-whisper` 或官方 `openai-whisper` 库实现。Whisper的多语言模型本身支持多种语言（包括中、英、日等）。提供不同模型大小（base, small, medium等）的选择，以平衡速度与精度。
            *   **(调研) 其他特定语言ASR方案：** 调研是否有针对特定目标语言（如中文、英文、日文）进行优化的、易于本地集成的开源或商业ASR SDK。
        *   **设备自动选择与手动切换：** 程序启动时自动检测并优先使用可用GPU（CUDA/MPS）；若无兼容GPU、驱动问题或检测失败，则默认使用CPU模式，并向用户给出相应提示。用户可随时在界面上手动切换至CPU模式或（若有可用GPU时）GPU模式。
        *   **(未来扩展) 在线ASR服务：** 预留接口，支持用户配置并使用云服务商API（如OpenAI API, Google Cloud Speech-to-Text, 或其他主流云服务商的多语言ASR API），需要用户自行提供API Key。早期版本可在UI中预留一个置灰的或标记为“未来功能”的API Key输入区域，以作提示。
    *   **输出：** 带精确时间戳（词级别或短语级别）的对应语言文本片段。

*   **3.4. 文本后处理与优化模块 (多语言环境)**
    *   **ASR结果规范化：**
        *   合并过于零碎的识别片段（例如，基于时间戳间隔和字符数的通用阈值，具体可配置）。
        *   基础标点符号补全（**需考虑不同语言的标点习惯，如中文的「。」、「，」，英文的`.`、`,`，日文的「。」、「、」等**）。可基于语音停顿或常见句末标记进行。
        *   去除常见的ASR识别错误或口头禅（**需考虑不同语言的情况**）。
    *   **自定义词典/替换规则 (多语言)：** 允许用户通过简单的文本文件（如CSV格式：`原文,替换文,语言代码(可选)` 或 JSON格式）配置多语言词典。规则应支持精确匹配，用于特定品牌名、术语、人名、常见错词修正等。
    *   **(可选) LLM增强模块 (多语言优化)：**
        *   通过OpenAI标准接口接入多个厂商的LLM（如GPT系列，或其他**对目标语言支持良好的LLM**）。
        *   **用户配置：**
            *   用户可以输入符合OpenAI格式的API Key。
            *   用户可以自定义请求URL（默认为OpenAI官方地址）。
            *   用户可以获取模型列表（如果API支持）或手动填写模型名称。
        *   **功能：** 智能标点、语法修正、文本润色、**可能的语体调整（视语言和需求而定）**。
        *   **异步处理：** 对于过长的字幕文件，需要进行异步处理，并考虑Token限制问题，可能需要对文本进行分块处理。
        *   此模块可由用户选择是否启用。
    *   **字幕断句与分行 (多语言)：**
        *   根据目标语言的语义、标点、时长、每行字数限制（可配置，**需考虑不同语言字符宽度差异，如中文全角、英文半角等**）等因素，智能地将文本切分为适合阅读的字幕行。断句时优先考虑在标点符号后或语义自然的停顿点进行。

*   **3.5. 字幕导出模块**
    *   **支持格式：**
        *   SRT (SubRip Text) - 核心支持
        *   LRC (LyRiCs) - 支持
        *   ASS (Advanced SubStation Alpha) - 支持基础格式，不含复杂样式。
    *   **文件编码：** 默认为UTF-8 (广泛支持多语言)。可考虑为特定语言或工具提供其他编码选项（如为日语提供Shift_JIS）。

*   **3.6. 用户界面 (UI) 模块 (Windows风格)**
    *   **类型：** 简洁易用的图形用户界面（桌面应用，使用PyQt5/6 或 CustomTkinter，确保Windows平台良好兼容性）。
    *   **核心操作：**
        *   文件/文件夹选择对话框（支持自定义输入/输出路径）。
        *   ASR引擎选择。
        *   Whisper模型大小选择。
        *   GPU/CPU模式切换。
        *   **AI设置选项:**
            *   (可选) LLM增强启用、API Key、URL、模型选择。
            *   (可选) 用户自定义System Prompt输入框 (多行文本，用于LLM上下文)。
        *   **高级设置选项:**
            *   (可选) 智能时间轴调整相关配置。
            *   (未来可添加其他高级参数设置)
        *   启动字幕生成过程。
        *   进度显示与状态反馈。
        *   **[待办] 字幕预览与编辑界面 (按DI值排序开发)：**
            *   **[TODO D1I0] 1. 字幕文本直接编辑**：允许直接修改字幕文本内容。
            *   **[TODO D2I0] 2. 字幕时间码精确调整 (D2I0)**：精确修改每条字幕的开始和结束时间。
            *   **[TODO D2I1] 3. 基本字幕操作 (D2I1)**：支持插入、删除字幕行。(合并、拆分待后续实现)
            *   **[待办] 4. 音频波形图显示与同步预览 (D3I1)**：可视化音频，帮助用户定位和调整字幕，播放音频时，对应字幕高亮或滚动显示。
        *   选择导出格式并下载字幕文件。
    *   **语言：** UI界面语言初期可为中文，未来计划支持英文、日文等更多语言。

**4. 非功能性需求**

*   **易用性：** 界面直观，操作简便，尽量减少用户配置负担。
*   **性能：**
    *   ASR处理速度：对于一段10分钟的标准AI日语音频，使用推荐的Whisper小型模型（如`small`），在主流消费级CPU（如Intel i5/AMD R5近三代产品）上应力争在2-3分钟内完成处理，在兼容的NVIDIA GPU（如GTX 1660/RTX 3050级别及以上）加速下应力争在30-60秒内完成。此为初步目标，具体视模型和硬件而定。
    *   UI响应：流畅不卡顿。
    *   **准确性：** 多语言ASR初始准确率高，LLM优化有效。
    *   **可配置性：** 核心参数（如ASR引擎、模型大小、LLM选项、输入输出路径、处理语言）可由用户选择和设置。
    *   **可扩展性：** 模块化设计，方便未来添加新的ASR引擎、LLM模型或导出格式。语言相关处理逻辑（如标点规则、断句策略、LLM prompts、UI特定本地化文本等）应尽可能封装为可配置的模块或独立的资源文件（如JSON, YAML），方便未来通过添加新的“语言包”来支持其他语言。
    *   **稳定性与错误处理：** 程序运行稳定，对常见错误有友好提示和处理机制。例如：
        *   输入文件格式不支持：清晰提示用户当前支持的格式列表。
        *   音频文件损坏或无法读取：提示文件可能已损坏或无读取权限。
        *   ASR模型文件缺失或损坏（本地ASR）：提示检查模型文件路径或重新下载/配置。
        *   （若使用在线服务）API Key无效或网络连接失败：提示检查API Key配置及网络连接状态。
        *   输出目录无写入权限：提示检查输出路径权限。
        *   不支持的语言选择：若用户选择了ASR模型或LLM不支持的语言，应给出提示。
    *   **资源占用：** 合理控制CPU、内存、显存占用。
    *   **平台兼容性：** 优先保证在Windows 10/11上的良好运行。

**5. 系统架构 (高层次) - (内部实现需考虑多语言特性)**

```
+---------------------+      +-------------------------+      +---------------------+
|     用户界面 (UI)   |----->|      输入/输出模块       |<---->|    配置管理器       |
| (Windows, 多语言支持) |      | (路径配置, 文件IO)      |      | (含多语言相关配置)    |
+---------------------+      +-------------------------+      +---------------------+
          ^                           |
          |                           v
          |      +---------------------------------------+
          |      |             音频预处理模块             |
          |      | (格式转换, 标准化, 降噪[低优])       |
          |      +---------------------------------------+
          |                           |
          |                           v
          |      +---------------------------------------+
          |      |        语音识别 (ASR) 模块            |
          |      | (Whisper[多语言], 其他ASR[调研])    |
          |      |  [GPU/CPU Aware]                      |
          |      +---------------------------------------+
          |                           |
          |                           v
          |      +---------------------------------------+
          |      |      文本后处理与优化模块 (多语言)        |
          |      | (规范化, 断句分行, LLM增强[可选])     |
          |      +---------------------------------------+
          |                           |
          v                           v
+---------------------+      +-------------------------+
|  (未来)字幕编辑器   |      |      字幕格式化与导出模块   |
+---------------------+      | (SRT, LRC, ASS)         |
                         +-------------------------+
```

**6. 技术栈选型**

*   **编程语言：** Python 3.9+
*   **ASR实现：**
    *   OpenAI Whisper: `faster-whisper` (推荐) 或 `openai-whisper` 官方库。**针对`faster-whisper`支持的多语言模型（如 `base`, `small`, `medium`）进行速度与准确性评估，为不同语言选择合适的默认模型或推荐。**
    *   **(调研项) 其他特定语言ASR SDK。**
*   **音频处理：** `ffmpeg-python` (或直接调用`ffmpeg`命令行), `pydub`, `noisereduce` (低优先级)。
*   **LLM接入：** `openai` Python库（用于兼容OpenAI API的各模型，**选择对目标语言处理能力强的模型**）。若未来考虑接入不完全兼容OpenAI API格式的特定语言LLM，需预留通过适配器模式或开发独立接入模块的可能性。
*   **字幕处理：** `pysrt` (SRT), 自定义逻辑 (LRC, ASS)。
*   **用户界面 (GUI)：** PyQt5/6 或 CustomTkinter (针对Windows优化)。建议在MVP阶段就倾向一个框架以减少后续重构。若追求快速原型和简洁界面，CustomTkinter可能更合适初期；若预期UI交互会变得更复杂或需要更多高级控件，PyQt可能是更长远的选择（但学习曲线和打包体积稍大）。**MVP阶段初步倾向使用CustomTkinter。**
*   **依赖管理：** `venv` + `pip` + `requirements.txt` 或 `Poetry` / `PDM`。
*   **打包 (桌面应用)：** PyInstaller 或 Nuitka (针对Windows ` .exe` 打包)。
*   **配置文件：** JSON或INI文件。默认优先尝试在用户操作系统的标准应用数据目录（例如Windows下的 `%APPDATA%\IntelliSubs`）中存储配置文件；若程序启动时在程序根目录下检测到特定标记文件（例如 `make_portable.txt` 或 `config_in_exe_dir.flag`），则视为便携模式，配置文件将存储在程序运行的根目录下。
*   **日志：** `logging`模块。

**7. 开发阶段与路线图 (初步，多语言侧重)**

*   **阶段一: MVP (Minimum Viable Product) - 多语言核心功能**
    *   **目标：** 实现针对标准多语言AI语音（初步支持中、英、日）的核心ASR转写与SRT导出功能。
    *   **功能：**
        *   MP3/WAV多语言音频输入 (中、英、日)。
        *   音频标准化与格式转换。
        *   集成 `faster-whisper` (选择合适的 `small` 或 `base` 多语言模型)，支持CPU/GPU自动检测与手动切换。
        *   用户可在UI选择处理语言（中、英、日）。
        *   基础ASR结果直接转换为SRT格式输出。
        *   简单的GUI (如CustomTkinter) 进行文件选择、路径配置、语言选择和启动。
        *   实现默认输入/输出文件夹及用户自定义功能。
    *   **产出：** 可用的基础多语言字幕生成工具。

*   **阶段二: 功能增强与多语言优化**
    *   **目标：** 完善核心功能，提升多语言处理效果和用户体验。
    *   **功能：**
        *   UI界面优化 (在MVP阶段选用的CustomTkinter基础上)，提供ASR模型大小选择（如 base, small, medium）。
        *   实现针对多语言的规则化文本后处理（标点、自定义词典）。
        *   实现针对多语言的智能断句与分行逻辑。
        *   支持LRC、ASS格式导出（考虑多语言编码）。
        *   视频文件音轨提取。
        *   扩展支持更多ASR语言（根据Whisper能力）。
    *   **产出：** 功能相对完善，易用的多语言字幕工具。

*   **阶段三: 高级功能、编辑与扩展**
    *   **目标：** 引入LLM增强，提升多语言字幕智能化水平，集成基础编辑功能，并提供灵活的配置选项。
    *   **功能：**
        *   **UI界面重构与功能调整 (设置面板):**
            *   将设置区域中原统一的“AI与高级设置”部分，拆分为两个独立的、更清晰的标签页或可折叠面板：“AI设置”和“高级设置”。
            *   **“AI设置”面板:**
                *   集成LLM增强模块（可选启用）的所有相关配置：
                    *   启用开关。
                    *   API Key输入。
                    *   API 请求URL自定义。
                    *   LLM模型选择（支持从API获取列表或用户手动输入）。
                *   新增**System Prompt输入功能**: 提供一个多行文本编辑框，允许用户输入自定义的系统级提示或上下文信息，以更精细地控制LLM的行为和输出风格。
                *   继续支持LLM的异步处理机制，以应对长文本处理和Token限制。
            *   **“高级设置”面板:**
                *   将原有的“智能时间轴调整”相关配置选项从主设置界面迁移至此面板。
                *   为未来可能增加的其他高级的、不常用的参数配置预留空间。
        *   **(可选) 支持导入参考脚本进行对比或辅助。**
        *   **[待办] 字幕编辑功能实现 (按DI值排序开发)：**
            *   **[TODO D1I0] 1. 字幕文本直接编辑**
            *   **[TODO D2I0] 2. 字幕时间码精确调整 (D2I0)**
            *   **[TODO D2I1] 3. 基本字幕操作 (D2I1)**（已实现插入、删除；合并、拆分待后续）
            *   **[待办] 4. 音频波形图显示与同步预览 (D3I1)**
        *   预留接口，为未来在线ASR服务集成做准备。
        *   更精细的错误处理和用户反馈，特别是在LLM调用失败或返回异常时。
    *   **产出：** 智能化的多语言字幕生成与编辑工具。

**8. 潜在风险与应对策略 (多语言相关)**

*   **多语言ASR准确率与特殊表达：**
    *   风险：不同语言的同音异义词、口语表达、特定方言或口音可能对ASR构成挑战。
    *   应对：优先选择Whisper的多语言模型中在目标语言上表现较好的版本；关注并调研是否有针对特定语言进行微调的开源Whisper模型或更专业的ASR SDK；LLM润色；自定义词典。
*   **多语言LLM选择与效果：**
    *   风险：并非所有LLM都对各种语言有同样优秀的理解和生成能力。
    *   应对：调研并列出对目标语言支持较好的LLM备选项；在实际集成前进行小规模测试对比其在标点、润色、语法修正等方面的效果。
*   **字符编码问题：**
    *   风险：多语言字符在不同系统和软件间可能因编码问题导致乱码。
    *   应对：默认统一使用UTF-8，为特定情况提供其他编码选项。在文件读写时明确指定编码。
*   **断句与分行逻辑的复杂性：**
    *   风险：不同语言的断句规则和排版习惯差异较大（如中文的按意群，英文的按语法，日文的考虑读点）。
    *   应对：为主要目标语言实现定制化的断句与分行策略，允许用户调整每行字数等参数。

**9. 测试策略概要**

*   **单元测试：** 针对核心功能模块（如音频格式转换、ASR接口调用、文本规范化函数、字幕格式化逻辑等）编写单元测试，确保各模块按预期工作。
*   **集成测试：**
    *   准备具有代表性的日语测试音频样本（涵盖不同语速、少量背景音、AI生成音轨特点）。
    *   定义预期的ASR转写结果和字幕格式输出。
    *   自动化或半自动化地进行端到端测试，验证从音频输入到字幕文件生成的完整流程。
*   **用户验收测试 (UAT)：** 由内部小编团队使用实际工作中的多语言音视频素材进行测试，重点评估易用性、准确性、性能以及与现有工作流的契合度。
*   **多语言特性测试：** 特别关注各目标语言ASR的准确性、标点符号的正确性、断句分行的自然度。

**10. 日志记录规范**

*   **日志级别：**
    *   `DEBUG`: 用于开发调试，记录详细的程序执行步骤、变量状态、函数调用等。
    *   `INFO`: 记录关键的用户操作（如文件选择、开始处理、导出字幕）、程序生命周期事件（启动、关闭）、重要状态变更（如切换CPU/GPU模式）。
    *   `WARNING`: 记录潜在问题或非严重错误，程序仍可继续运行（如可选模块加载失败但核心功能可用、特定配置项无效等）。
    *   `ERROR`: 记录导致功能失败或程序异常的错误（如文件读写失败、ASR引擎初始化失败、API调用严重错误、未捕获的异常等）。
*   **日志内容：** 日志应包含时间戳、日志级别、模块名（或函数名）、以及清晰描述事件的消息。错误日志应尽可能包含错误类型和堆栈跟踪信息。
*   **日志输出：** 默认输出到用户应用数据目录下的日志文件（如 `IntelliSubs.log`），可按日期滚动或大小限制分割。UI界面可提供查看最新日志或打开日志文件夹的便捷方式。
*   **用户反馈：** 鼓励用户在遇到问题时附上日志文件，以便快速定位问题。

**11. 依赖管理与打包 (补充)**

*   **ASR模型文件：** 打包时，默认的、推荐的 `faster-whisper` 模型文件（如 `small` 模型）应作为程序资源一同打包进最终的可执行文件或安装包中，或在首次运行时提示用户自动下载到指定位置。用户选择其他模型时，程序应能正确加载用户指定路径的模型文件。
*   **FFmpeg依赖：** 若直接调用 `ffmpeg` 命令行，需确保用户系统已安装 `ffmpeg` 并配置到环境变量，或在程序包内集成一个便携版的 `ffmpeg`，并在调用时指定其路径。使用 `ffmpeg-python` 库通常能更好地管理此依赖。
*   **Windows打包目标：** 生成单一的 `.exe` 可执行文件（若可能，通过Nuitka配合静态链接或PyInstaller的 `--onefile` 模式），或一个包含主程序及所有依赖DLL的文件夹（绿色版）。提供 `.msi` 或 `.exe` 安装程序更佳。

**12. API Key 安全 (未来在线服务相关)**

*   **本地存储：** 用户提供的第三方服务API Key（如OpenAI API Key）将仅存储在用户本地计算机的配置文件中（例如，在第6节描述的配置文件内）。
*   **不上传：** 程序不会将用户API Key上传到开发者服务器或任何其他未经用户明确同意的远程位置。
*   **简单加密（可选考虑）：** 为增强本地存储的安全性，可考虑对配置文件中存储的API Key进行简单的对称加密（密钥可基于用户机器码生成或由用户设置一个主密码），但这会增加实现的复杂度。MVP阶段可暂不实现，但需在文档中提示用户自行妥善保管API Key。
*   **明示责任：** 在UI界面和文档中明确告知用户，API Key的安全性主要由用户负责，尤其是在共享计算机上使用时。建议用户使用独立的、权限受限的API Key。

**13. Future UI Enhancements (待办 UI 改进)**

*   **全局动态字体大小**：实现应用内所有相关组件的字体大小能根据主窗口尺寸动态调整，并设定合理的最小和最大字号限制，以提升不同分辨率下的可读性。
*   **高级响应式布局调整**：
    *   解决窗口缩小时底部状态栏可能被遮挡或完全不可见的问题，确保其核心信息（如状态文本）始终可见或优雅降级。
    *   解决窗口缩小时“处理结果”列表和“字幕预览”编辑区域可能被过度压缩的问题，确保其内容在小窗口尺寸下仍具有基本可用性。
    *   探索使用更灵活的布局技术或事件绑定来动态管理组件尺寸和可见性。
*   **界面布局调整 (本次开发内容):**
    *   将“已选文件列表”块和“处理结果”块合并到主窗口的右上角区域，形成一个统一的信息展示区。
    *   缩短“选择文件”、“输出目录”、“开始生成字幕”按钮所在的顶部控制栏的高度，使其更紧凑。
    *   调整整体布局，将左侧区域主要用于核心控制和设置，右侧区域用于文件列表和结果展示/编辑，底部区域用于状态栏和导出操作。
*   **自适应布局与尺寸分配：**
    *   移除或替换现有UI中基于像素(pixel)的硬编码尺寸设置。
    *   采用CustomTkinter的布局权重 (`grid_rowconfigure`, `grid_columnconfigure` with `weight`) 和 `sticky` 选项，以及可能的百分比或比例分配方式，使各主要UI区域（如左侧控制区、右侧信息区、底部预览/编辑区）能根据窗口总尺寸按比例自适应分配空间。
    *   确保在窗口缩放时，各组件能平滑地调整大小和位置，保持界面的协调性和可用性。
