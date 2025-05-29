# Configuration Management Utility
import json
import os
import logging

DEFAULT_CONFIG_FILENAME = "config.json"
DEFAULT_APP_DATA_SUBDIR = "IntelliSubs" # Subdirectory in user's app data folder

class ConfigManager:
    def __init__(self, config_file_path: str = None, use_app_data_dir: bool = False, # Changed default for use_app_data_dir
                 project_root_dir: str = None, logger: logging.Logger = None):
        """
        Initializes the ConfigManager.

        Args:
            config_file_path (str, optional): Specific path to the config file. If None, a default path will be used.
            use_app_data_dir (bool): If True and config_file_path is None, uses user's application data directory.
                                     If False (default), uses project_root_dir.
            project_root_dir (str, optional): The root directory of the project. Required if use_app_data_dir is False
                                              and config_file_path is None.
            logger (logging.Logger, optional): Logger instance. If None, a new logger is used.
        """
        self.logger = logger if logger else logging.getLogger(__name__)

        if config_file_path:
            self.config_path = os.path.abspath(config_file_path)
        elif use_app_data_dir:
            config_dir_to_use = ""
            try:
                app_data = os.getenv('APPDATA') or os.getenv('LOCALAPPDATA')
                if app_data:
                    config_dir_to_use = os.path.join(app_data, DEFAULT_APP_DATA_SUBDIR)
                else:
                    self.logger.warning("APPDATA environment variable not found. Falling back to project root for config.")
                    if not project_root_dir:
                        # Determine project root based on this file's location if not provided
                        # utils is under intellisubs, so ../../ should be project root
                        project_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
                        self.logger.info(f"Inferred project_root_dir as: {project_root_dir}")
                    config_dir_to_use = project_root_dir
            except Exception as e:
                self.logger.error(f"Error determining app data directory: {e}. Falling back to project root.", exc_info=True)
                if not project_root_dir:
                    project_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
                config_dir_to_use = project_root_dir
            
            if config_dir_to_use and not os.path.exists(config_dir_to_use):
                try:
                    os.makedirs(config_dir_to_use, exist_ok=True)
                    self.logger.info(f"Created config directory: {config_dir_to_use}")
                except Exception as e:
                    self.logger.error(f"Error creating config directory {config_dir_to_use}: {e}. Using current dir as fallback.", exc_info=True)
                    config_dir_to_use = "." # Fallback
            self.config_path = os.path.join(config_dir_to_use, DEFAULT_CONFIG_FILENAME)

        elif project_root_dir:
            self.config_path = os.path.join(os.path.abspath(project_root_dir), DEFAULT_CONFIG_FILENAME)
        else:
            # Fallback if project_root_dir is also None and not using app_data_dir
            # (should be provided by the app)
            self.logger.warning("ConfigManager: Neither specific path, app_data_dir, nor project_root_dir provided. Defaulting config to current directory.")
            self.config_path = os.path.join(".", DEFAULT_CONFIG_FILENAME)
 
        self.logger.info(f"ConfigManager initialized. Config file path: {self.config_path}")
        self.default_config = self.get_default_settings()

    def get_default_settings(self) -> dict:
        """Returns the default application settings."""
        return {
            "asr_model": "small", # "tiny", "base", "small", "medium", "large-v2", etc.
            "asr_device": "cpu",  # "cpu" or "cuda" (or "mps" for Mac if supported by backend)
            "asr_compute_type": "float32", # for faster-whisper: "float16", "int8", "int8_float16"
            
            "llm_enabled": False,
            "llm_provider": "openai", # or "local_gpt", "custom_api"
            "llm_model_name": "gpt-3.5-turbo",
            "llm_api_key": "", # Store securely or prompt user
            "llm_base_url": None, # For custom OpenAI-compatible APIs
            "llm_system_prompt": "", # User override for system prompt (from UI)
            "llm_script_context": "", # For providing script context to LLM
            "llm_prompts": {
                "ja": {
                    "system": (
                        "あなたは日本語のビデオ字幕編集の専門家です。"
                        "以下のテキストを自然で読みやすい日本語字幕に最適化し、句読点を適切に調整し、明瞭さを向上させてください。"
                        "応答には最適化された字幕テキスト「のみ」を含めてください。説明、マークダウン、書式設定、または「最適化された字幕:」のようなラベルは一切含めないでください。"
                        "必ず结果を返し、空の応答を避けてください。\n"
                        "例: 入力: 'こんにちは皆さん元気？' → 出力: 'こんにちは、皆さん。元気ですか？'"
                    ),
                    "user_template": "テキスト：「{text_to_enhance}」"
                },
                "zh": {
                    "system": (
                        "你是一位专业的视频字幕编辑。请优化以下文本，使其成为自然流畅、标点准确的简体中文视频字幕。"
                        "主要任务包括：修正明显的ASR识别错误（如果能判断），补全或修正标点符号（特别是句号、逗号、问号），"
                        "并确保文本在语义上通顺且易于阅读。"
                        "返回结果时，请「仅」包含优化后的字幕文本。不要添加任何解释、markdown、格式化内容或类似“优化字幕:”的标签。"
                        "请确保结果非空。\n"
                        "输入示例：'大家好今天天气不错我们去公园玩吧' -> 输出示例：'大家好，今天天气不错。我们去公园玩吧！'"
                    ),
                    "user_template": "原始文本：“{text_to_enhance}”"
                },
                "en": { # Fallback for English or other unspecified languages
                    "system": (
                        "You are an expert in subtitle editing. Optimize the following text for natural, readable subtitles, "
                        "adjusting punctuation and improving clarity. "
                        "In your response, include *only* the optimized subtitle text. Do not add any explanations, markdown, formatting, or labels like 'Optimized Subtitle:'."
                        "Ensure a result is returned and avoid empty responses.\n"
                        "Example: Input: 'hello everyone hows it going' -> Output: 'Hello, everyone. How's it going?'"
                    ),
                    "user_template": "Text: \"{text_to_enhance}\""
                }
            },

            "output_directory": "output", # Relative to where user runs from, or allow absolute
            "default_export_format": "srt",
            "language": "ja", # Default processing language

            "ui_theme": "System", # "System", "Light", "Dark"
            "ui_scaling": "100%", # e.g., "80%", "100%", "120%"
            
            # Paths to user's custom dictionaries for each supported language
            "custom_dictionary_path_ja": "",
            "custom_dictionary_path_zh": "",
            "custom_dictionary_path_en": "", # Add other languages as needed

            "auto_open_output_dir": False, # Whether to open output dir after export
            "log_level": "INFO" # DEBUG, INFO, WARNING, ERROR
        }

    def load_config(self) -> dict:
        """Loads configuration from the JSON file. Returns defaults if file not found or invalid."""
        if not os.path.exists(self.config_path):
            self.logger.info(f"Config file not found at {self.config_path}. Using default settings.")
            return self.default_config.copy()
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)
            # Merge loaded settings with defaults to ensure all keys are present
            config = self.default_config.copy()
            config.update(loaded_settings) # Loaded settings override defaults
            self.logger.info(f"Configuration loaded from {self.config_path}")
            return config
        except json.JSONDecodeError:
            self.logger.error(f"Error decoding JSON from {self.config_path}. Using default settings.", exc_info=True)
            return self.default_config.copy()
        except Exception as e:
            self.logger.error(f"Error loading config from {self.config_path}: {e}. Using default settings.", exc_info=True)
            return self.default_config.copy()

    def save_config(self, settings: dict):
        """Saves the given settings dictionary to the JSON config file."""
        try:
            # Ensure the directory for the config file exists
            config_dir = os.path.dirname(self.config_path)
            if not os.path.exists(config_dir) and config_dir: # Check if config_dir is not empty string
                os.makedirs(config_dir, exist_ok=True)

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            self.logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            self.logger.error(f"Error saving configuration to {self.config_path}: {e}", exc_info=True)

if __name__ == '__main__':
    # Example Usage:
    
    # Example Usage:
    # Initialize logging for testing ConfigManager directly
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    test_logger = logging.getLogger("TestConfigManager")

    # 1. Default path (tries APPDATA/IntelliSubs/config.json or similar)
    cm_default = ConfigManager(logger=test_logger)
    cfg_default = cm_default.load_config()
    test_logger.info(f"Default loaded config: {cfg_default}")
    cfg_default["asr_model"] = "medium" # Change a setting
    cfg_default["new_setting_test"] = True
    cm_default.save_config(cfg_default)
    test_logger.info(f"Default config saved to: {cm_default.config_path}")

    # 2. Specific path
    # cm_specific = ConfigManager(config_file_path="test_app_config.json")
    # cfg_specific = cm_specific.load_config()
    # print("\nSpecific path loaded config:", cfg_specific)
    # cfg_specific["llm_enabled"] = True
    # cfg_specific["llm_api_key"] = "test_key_123"
    # cm_specific.save_config(cfg_specific)
    # if os.path.exists("test_app_config.json"):
    #     print("Specific config saved to test_app_config.json")
        # os.remove("test_app_config.json") # Clean up

    # 3. Using program directory explicitly (not user app data)
    # cm_local = ConfigManager(use_app_data_dir=False)
    # cfg_local = cm_local.load_config()
    # print(f"\nLocal dir config loaded from {cm_local.config_path}:", cfg_local)
    # cfg_local["language"] = "en"
    # cm_local.save_config(cfg_local)

    # Test loading non-existent defaults
    # if os.path.exists(cm_default.config_path):
    #    os.remove(cm_default.config_path)
    # cfg_reloaded_defaults = cm_default.load_config()
    # print("\nConfig after deleting and reloading (should be defaults):", cfg_reloaded_defaults)