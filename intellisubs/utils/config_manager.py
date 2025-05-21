# Configuration Management Utility
import json
import os
import logging

DEFAULT_CONFIG_FILENAME = "config.json"
DEFAULT_APP_DATA_SUBDIR = "IntelliSubs" # Subdirectory in user's app data folder

class ConfigManager:
    def __init__(self, config_file_path: str = None, use_app_data_dir: bool = True, logger: logging.Logger = None):
        """
        Initializes the ConfigManager. Accepts a logger instance.

        Args:
            config_file_path (str, optional): Specific path to the config file. If None, a default path will be used.
            use_app_data_dir (bool): If True and config_file_path is None, tries to use a subdirectory in the user's
                                     application data directory. Falls back to program's directory if app data dir is not found.
            logger (logging.Logger, optional): Logger instance. If None, a new logger named after the module will be used.
        """
        self.logger = logger if logger else logging.getLogger(__name__)

        if config_file_path:
            self.config_path = config_file_path
        else:
            config_dir_to_use = ""
            if use_app_data_dir:
                try:
                    app_data = os.getenv('APPDATA') or os.getenv('LOCALAPPDATA')
                    if app_data:
                        config_dir_to_use = os.path.join(app_data, DEFAULT_APP_DATA_SUBDIR)
                    else: # Fallback if APPDATA is not set
                        self.logger.warning("APPDATA environment variable not found. Using program directory for config.")
                        config_dir_to_use = os.path.dirname(os.path.abspath(__file__)) # Or a known base dir
                except Exception as e:
                    self.logger.error(f"Error determining app data directory: {e}. Using program directory.", exc_info=True)
                    config_dir_to_use = os.path.dirname(os.path.abspath(__file__))
            else: # Use program's directory (or relative to it)
                # Assuming this util is one level down from project root if not using app_data
                script_dir = os.path.dirname(os.path.abspath(__file__))
                config_dir_to_use = os.path.join(script_dir, "..") # Adjust if utils is elsewhere

            if not os.path.exists(config_dir_to_use):
                try:
                    os.makedirs(config_dir_to_use, exist_ok=True)
                    self.logger.info(f"Created config directory: {config_dir_to_use}")
                except Exception as e:
                    self.logger.error(f"Error creating config directory {config_dir_to_use}: {e}. Config may not save.", exc_info=True)
                    # Fallback to an even simpler local path if directory creation fails
                    config_dir_to_use = "."

            self.config_path = os.path.join(config_dir_to_use, DEFAULT_CONFIG_FILENAME)
 
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

            "output_directory": "output", # Relative to where user runs from, or allow absolute
            "default_export_format": "srt",
            "language": "ja", # Default processing language

            "ui_theme": "System", # "System", "Light", "Dark"
            "ui_scaling": "100%", # e.g., "80%", "100%", "120%"

            "custom_dictionary_path": "", # Path to user's custom dictionary
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