# 文档结构规划

本规划旨在为 "智字幕 (IntelliSubs)" 项目建立一个清晰、全面且易于维护的文档体系。文档是项目成功的重要组成部分，服务于最终用户、开发者以及其他相关人员。

## 1. 根目录文档

这些是项目顶层的关键文档，提供高级信息和入口点。

*   **`README.md`**
    *   **目标读者:** 最终用户、开发者、潜在贡献者。
    *   **内容:**
        *   项目名称和一句话核心价值主张。
        *   项目状态徽章 (例如：构建状态, 测试覆盖率, 最新版本号 - 可选，后期集成CI/CD后添加)。
        *   简要介绍项目旨在解决的问题以及其核心功能亮点。
        *   Windows平台下的快速安装指南 (如何获取安装包或绿色版，如何运行)。
        *   一个最基本的使用案例或快速上手步骤。
        *   如何寻求帮助或报告程序中遇到的问题 (例如，指向 `docs/troubleshooting.md` 或Issue提交通道)。
        *   指引到更详细文档的链接 (例如，用户手册 [`docs/user_manual/index.md`](docs/user_manual/index.md), 开发者指南 [`docs/developer_guide/index.md`](docs/developer_guide/index.md))。
        *   简要的许可证信息 (例如 "采用 MIT 许可证分发") 并链接到 `LICENSE` 文件。

*   **`DEVELOPMENT.md`** (已创建并优化)
    *   **目标读者:** 项目核心开发者、产品经理、架构师。
    *   **内容:** (详细内容已在该文件中)
        *   此文档侧重于项目的需求定义、设计决策、技术选型、演进路线图以及相关的质量保障策略。它是项目开发的“蓝图”。

*   **`PROJECT_STRUCTURE.md`** (已创建)
    *   **目标读者:** 开发者。
    *   **内容:** (详细内容已在该文件中)
        *   提供项目代码和文件的目录结构图示及其详细说明，帮助开发者快速理解代码的组织方式和各部分职责。

*   **`CONTRIBUTING.md`**
    *   **目标读者:** 希望为本项目贡献代码、文档或其他改进的外部或内部开发者。
    *   **内容:**
        *   欢迎辞和贡献的重要性。
        *   如何设置本地开发环境的简要步骤 (详细步骤可链接到 [`docs/developer_guide/setup_env.md`](docs/developer_guide/setup_env.md))。
        *   代码风格指南 (或链接到 [`docs/developer_guide/coding_standards.md`](docs/developer_guide/coding_standards.md))。
        *   提交贡献的流程 (例如：如何Fork项目, 创建特性分支, 编写提交信息, 发起Pull Request)。
        *   Issue和Pull Request的命名约定和模板建议。
        *   项目的行为准则 (Code of Conduct)，确保一个友好和协作的社区环境。

*   **`LICENSE`**
    *   **目标读者:** 所有用户和开发者。
    *   **内容:** 项目所采用的开源许可证的完整文本 (例如 MIT License, Apache License 2.0)。

## 2. `docs/` 目录下的详细文档

此目录存放更具体和深入的文档内容，可以按目标读者或主题进行组织。

### 2.1. `docs/user_manual/` (用户手册)

*   **目标读者:** 应用程序的最终用户 (例如，公司内部的新媒体小编、视频剪辑师)。
*   **`index.md`**: 用户手册的入口页面，包含手册内容概览和导航。
*   **`installation.md`**:
    *   详细的安装步骤：如何下载和运行 `.exe` 安装包，或如何使用绿色解压版。
    *   程序运行所需的系统环境 (例如，Windows 10/11, 特定版本的 .NET Framework 或 VC++ Redistributable 如果打包时未完全包含)。
    *   首次运行时的必要配置步骤（如果有）。
*   **`quick_start.md`**:
    *   一个简单明了的端到端操作示例，引导用户快速完成一次从音频输入到字幕导出的完整流程。
    *   应用程序主界面的主要区域和核心操作按钮介绍。
*   **`features/`**: (可以将每个主要功能拆分为单独的 .md 文件，便于维护和阅读)
    *   **`input_output.md`**: 如何选择和管理输入音视频文件/文件夹，如何配置输出路径。
    *   **`asr_settings.md`**: 如何选择ASR引擎 (若未来支持多个), Whisper模型大小，以及CPU/GPU模式切换。
    *   **`reference_script.md`**: (可选)参考脚本功能的使用说明。
    *   **`llm_enhancement.md`**: 如何启用和配置LLM增强模块，API Key的设置。
    *   **`custom_dictionary.md`**: 如何创建、配置和使用自定义词典。
    *   **`subtitle_export.md`**: 不同字幕格式 (SRT, LRC, ASS) 的导出选项和注意事项。
    *   **`preview.md`**: 如何使用字幕预览功能。
*   **`faq.md`** (可选，也可整合进 `troubleshooting.md`):
    *   针对用户常见问题的解答列表。

### 2.2. `docs/developer_guide/` (开发者指南)

*   **目标读者:** 项目的开发者、维护者以及对技术实现感兴趣的人员。
*   **`index.md`**: 开发者指南的入口页面，包含指南内容概览和导航。
*   **`setup_env.md`**:
    *   搭建完整开发环境的详细步骤：所需的Python版本，如何使用 `requirements.txt` 或 `pyproject.toml` 安装依赖，推荐的IDE (如VS Code) 及其相关插件和配置建议。
    *   如何运行单元测试和集成测试。
    *   如何在开发模式下启动和调试应用程序。
*   **`coding_standards.md`**:
    *   代码风格规范：遵循PEP 8，统一的命名约定 (变量, 函数, 类, 模块)，注释的最佳实践和要求。
    *   推荐使用的linter (如Flake8, Pylint) 和formatter (如Black, autopep8) 的配置方法。
    *   Git提交信息的规范 (例如，Conventional Commits)。
*   **`architecture/`**: (可以将不同层面的架构设计拆分)
    *   **`overview.md`**: 高层次的系统架构图和组件交互说明 (可复用或细化 `DEVELOPMENT.md` 中的架构图)。
    *   **`core_modules.md`**: 对 `intellisubs/core/` 目录下各核心模块 (ASR服务, 音频处理, 文本处理, 字幕格式化, 工作流管理等) 的详细设计文档。包括：
        *   每个模块的主要职责和边界。
        *   关键类图和主要的公共接口 (API)。
        *   模块之间的数据流和交互方式。
        *   重要算法、设计模式或第三方库的使用说明。
    *   **`ui_design.md`**: UI模块 (`intellisubs/ui/`) 的架构思路，视图-模型分离 (如果采用)，主要UI组件的设计和事件处理机制。
*   **`guides/`**: (针对特定开发任务的指南)
    *   **`adding_new_asr_engine.md`**: 详细步骤说明如何为系统集成一个新的ASR引擎。
    *   **`extending_subtitle_formats.md`**: 如何为应用添加对新的字幕导出格式的支持。
*   **`build_and_packaging.md`**:
    *   如何使用项目提供的打包脚本 (例如 `scripts/build_app.py`) 或直接通过 PyInstaller/Nuitka 来构建Windows可执行文件 (`.exe`) 或安装包的详细说明。
    *   不同打包选项的解释和注意事项 (例如，单文件模式 vs. 文件夹模式，包含/排除特定依赖)。

### 2.3. `docs/api_reference/` (API 参考 - 根据需要创建)

*   **目标读者:** 主要为开发者，特别是那些需要直接与项目的核心模块进行编程交互的场景 (例如，其他系统集成此项目的核心库)。
*   **内容:**
    *   通常建议使用工具（如 Sphinx 配合 `sphinx.ext.autodoc` 和 `sphinx.ext.napoleon`）从Python代码中的docstrings自动生成。
    *   清晰地列出所有公共的类、方法、函数及其参数说明、类型提示、返回值和可能抛出的异常。
    *   (对于初期的桌面应用，如果核心逻辑不作为库被外部调用，此部分的优先级可以稍低，但良好的docstrings是必需的。)

### 2.4. `docs/troubleshooting.md` (故障排除指南)

*   **目标读者:** 最终用户、技术支持人员、开发者。
*   **内容:**
    *   列出用户在使用过程中可能遇到的常见错误信息、警告或异常行为。
    *   针对每个问题，提供可能的原因分析和具体的排查步骤或解决方法。
    *   关于性能问题的初步排查建议 (例如，检查CPU/GPU占用，模型大小选择等)。
    *   如何解读和使用应用程序生成的日志文件 (`logging`模块输出) 来辅助定位问题。
    *   当用户无法自行解决问题时，如何有效地报告问题 (例如，需要提供哪些信息：操作系统版本，软件版本，错误截图，复现步骤，相关日志等)。

## 3. 文档工具和格式

*   **首选格式:** Markdown (`.md`)，因其简洁易学、纯文本易于版本控制，并且被广泛的工具和平台支持。
*   **图表工具 (可选):**
    *   使用 **draw.io (diagrams.net)** 或桌面版 draw.io 创建流程图、架构图、类图等，然后导出为PNG或SVG格式嵌入到Markdown文件中。
    *   或者，使用文本描述性绘图工具如 **PlantUML** 或 **Mermaid**，可以直接在Markdown中编写图表代码，某些Markdown渲染器或文档生成工具可以直接渲染它们。
*   **文档生成工具 (可选，推荐用于`docs/`目录):**
    *   **MkDocs**: Python编写的静态站点生成器，配置简单，主题美观，非常适合Markdown项目文档。可以使用 `mkdocs-material` 主题以获得更好的外观和功能。
    *   **Sphinx**: 功能更强大的Python文档生成器，支持reStructuredText和Markdown (通过 `myst_parser`)，尤其适合生成API参考文档。学习曲线稍陡峭。
    *   这些工具可以将 `docs/` 目录下的Markdown文件构建成一个易于导航、可搜索的静态HTML文档网站，提升文档的可读性和专业性。

此文档结构旨在为项目的不同阶段和不同角色的信息需求提供支持，并随着项目的发展而持续更新和完善。