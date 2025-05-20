# 项目目录结构建议

本项目 "智字幕 (IntelliSubs)" 建议采用以下目录结构，以支持企业级应用的开发、维护和扩展需求。

```
intelli_subs/
├── intellisubs/                  # 主应用程序源代码包
│   ├── __init__.py
│   ├── core/                     # 核心逻辑：ASR、文本处理、音频处理等
│   │   ├── __init__.py
│   │   ├── asr_services/         # ASR引擎的具体实现 (例如 Whisper, 未来可能的其他引擎)
│   │   │   ├── __init__.py
│   │   │   ├── base_asr.py       # ASR服务基类
│   │   │   └── whisper_service.py  # Whisper封装实现
│   │   ├── audio_processing/     # 音频预处理模块
│   │   │   ├── __init__.py
│   │   │   └── processor.py
│   │   ├── text_processing/      # 文本后处理与优化模块
│   │   │   ├── __init__.py
│   │   │   ├── normalizer.py     # ASR结果规范化
│   │   │   ├── punctuator.py     # 标点恢复
│   │   │   ├── segmenter.py      # 字幕断句与分行
│   │   │   └── llm_enhancer.py   # LLM增强模块
│   │   ├── subtitle_formats/     # 字幕格式处理 (SRT, LRC, ASS)
│   │   │   ├── __init__.py
│   │   │   ├── base_formatter.py
│   │   │   ├── srt_formatter.py
│   │   │   ├── lrc_formatter.py
│   │   │   └── ass_formatter.py
│   │   └── workflow_manager.py   # 协调核心处理流程
│   ├── ui/                       # 用户界面 (CustomTkinter)
│   │   ├── __init__.py
│   │   ├── app.py                # 主应用类，管理窗口和事件
│   │   ├── views/                # UI窗口和主要视图
│   │   │   ├── __init__.py
│   │   │   └── main_window.py
│   │   ├── widgets/              # 自定义UI组件
│   │   │   ├── __init__.py
│   │   │   └── file_dialogs.py
│   │   └── assets/               # UI静态资源 (图标, 图片 - 如果需要)
│   │       └── icons/
│   ├── utils/                    # 通用工具函数、辅助类
│   │   ├── __init__.py
│   │   ├── file_handler.py     # 文件操作工具
│   │   ├── logger_setup.py     # 日志配置
│   │   └── config_manager.py   # 应用程序配置管理
│   ├── resources_rc.py           # Qt Designer 资源文件 (如果使用PyQt并转换.qrc)
│   └── main.py                   # 应用程序入口点
├── tests/                        # 单元测试和集成测试
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── asr_services/
│   │   │   └── test_whisper_service.py
│   │   └── text_processing/
│   │       └── test_segmenter.py
│   └── ui/
│       ├── __init__.py
│       └── # (UI测试可能需要特定框架如pytest-qt或模拟)
├── docs/                         # 项目文档 (除了根目录的MD文件)
│   ├── index.md                  # 文档首页 (如果使用MkDocs/Sphinx等工具生成)
│   ├── user_manual/              # 用户手册
│   │   ├── installation.md
│   │   ├── quick_start.md
│   │   └── features.md
│   ├── developer_guide/          # 开发者指南
│   │   ├── setup_env.md
│   │   ├── coding_standards.md
│   │   └── module_architecture.md # 各模块详细设计
│   ├── api_reference/            # API文档 (可由代码注释自动生成)
│   │   └── core.md
│   └── troubleshooting.md        # 故障排除指南
├── scripts/                      # 辅助脚本 (例如：打包、代码检查、模型下载)
│   ├── build_app.py              # 打包脚本 (调用PyInstaller/Nuitka)
│   ├── lint.sh                   # 代码风格检查脚本
│   └── download_models.py        # 下载默认ASR模型的脚本
├── resources/                    # 应用程序使用的非代码资源
│   ├── default_models/           # 默认ASR模型文件 (例如 Whisper base/small)
│   │   └── faster_whisper_small_ja/
│   ├── custom_dictionaries/      # 默认自定义词典示例 (日语)
│   │   └── jp_custom_dict.csv
│   ├── i18n/                     # 国际化/本地化文件 (如果未来支持多语言UI)
│   │   ├── en_US.json
│   │   └── ja_JP.json
│   └── app_icon.ico              # 应用程序图标
├── .gitignore                    # Git忽略规则
├── LICENSE                       # 项目许可证 (例如 MIT, Apache 2.0)
├── README.md                     # 项目概览, 安装指南, 快速上手 (面向最终用户和开发者)
├── DEVELOPMENT.md                # (已存在并优化，偏向需求和设计决策)
├── CONTRIBUTING.md               # 贡献指南 (面向希望参与开发的贡献者)
├── requirements.txt              # Python依赖项列表
├── pyproject.toml                # (可选, 用于更现代的Python项目管理如Poetry/PDM, 或PEP 517/518)
└── setup.py                      # (可选, 如果使用setuptools进行打包)
```

## 结构说明

*   **`intellisubs/`**: 核心应用代码。
    *   **`core/`**: 包含所有后端处理逻辑，如ASR集成、音频处理、文本后处理、字幕生成等。
    *   **`ui/`**: 包含所有用户界面相关的代码，基于选定的GUI框架（如CustomTkinter）。
    *   **`utils/`**: 包含通用的辅助函数和类，如文件操作、日志、配置管理。
    *   **`main.py`**: 应用的启动入口。
*   **`tests/`**: 存放所有自动化测试。其内部结构应大致映射 `intellisubs/` 包的结构，以便于组织和查找测试用例。
*   **`docs/`**: 存放除根目录下 `README.md`, `DEVELOPMENT.md`, `CONTRIBUTING.md` 之外的所有详细文档。
    *   `user_manual/`: 面向最终用户的使用说明。
    *   `developer_guide/`: 面向开发者的技术文档，包括环境搭建、编码规范、模块设计等。
    *   `api_reference/`: （可选）如果核心模块提供API，这里可以存放自动生成的API文档。
    *   `troubleshooting.md`: 常见问题与解决方法。
*   **`scripts/`**: 包含用于开发、构建、部署或维护的辅助脚本。
*   **`resources/`**: 存放应用运行所需的静态资源，如默认的ASR模型文件、图标、示例自定义词典、国际化文件等。这些资源通常不直接参与编译，但在打包或运行时会被程序引用。
*   **根目录文件**:
    *   `.gitignore`: 指定Git版本控制忽略的文件和目录。
    *   `LICENSE`: 项目的开源许可证。
    *   `README.md`: 项目的入口文档，提供概览、安装和基本使用说明。
    *   `DEVELOPMENT.md`: （已存在）详细的需求分析、设计决策、技术选型等，偏重于项目规划和演进。
    *   `CONTRIBUTING.md`: 为希望向项目贡献代码的开发者提供指南。
    *   `requirements.txt`: 列出项目运行所需的所有Python依赖包及其版本。
    *   `pyproject.toml` / `setup.py`: （可选）用于Python项目打包和分发的相关配置文件。

这个结构旨在提高项目的模块化程度、可测试性和可维护性。