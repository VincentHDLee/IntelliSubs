# Configuration Management

Effective configuration management is crucial for 智字幕 (IntelliSubs) to allow users to customize its behavior and for the application to store its state and preferences persistently. This is primarily handled by the `ConfigManager` utility.

*(Refer to `intellisubs/utils/config_manager.py` for the implementation.)*

## Goals of Configuration Management

*   **Persistence:** User settings should persist across application sessions.
*   **Defaults:** Provide sensible default settings so the application works out-of-the-box.
*   **User Customization:** Allow users to easily modify settings through the UI.
*   **Accessibility:** Configuration should be accessible to different parts of the application (core logic, UI).
*   **Robustness:** Handle cases where the config file is missing, corrupted, or contains partial data.

## `ConfigManager` (`intellisubs/utils/config_manager.py`)

*   **Role:** This class is responsible for loading configuration settings from a file, providing default settings if the file doesn't exist or is invalid, and saving settings back to the file.
*   **Configuration File Format:**
    *   **JSON (JavaScript Object Notation):** Chosen for its human-readability, ease of parsing in Python (via the `json` module), and widespread use.
    *   File name: `config.json` (default).
*   **Configuration File Location:**
    *   **Primary (User-Specific):** The manager attempts to store `config.json` in a dedicated subdirectory within the user's standard application data directory to keep user-specific settings separate and maintain a clean program directory.
        *   Windows: `%APPDATA%\IntelliSubs\config.json` or `%LOCALAPPDATA%\IntelliSubs\config.json`.
    *   **Fallback (Portable Mode / No AppData):** If the application data directory cannot be determined or written to, or if a "portable mode" is explicitly triggered (e.g., by the presence of a specific flag file in the app's root directory, as mentioned in `DEVELOPMENT.md`), the `config.json` will be stored in the application's root directory (or a subdirectory like `config/` within it). This makes the application self-contained.
    *   The `ConfigManager` constructor logic handles determining the appropriate path.
*   **Key Methods:**
    *   `__init__(config_file_path: Optional[str], use_app_data_dir: bool)`:
        *   Determines the final `self.config_path`.
        *   Loads `self.default_config` by calling `get_default_settings()`.
    *   `get_default_settings() -> dict`:
        *   Defines a dictionary containing all possible configuration keys and their default values. This serves as the canonical list of settings.
        *   Example default settings include ASR model, device, LLM toggle, API keys (empty by default), UI theme, paths, etc. (Refer to `DEVELOPMENT.md` or the `ConfigManager` code for a full list).
    *   `load_config() -> dict`:
        *   Attempts to read and parse `config.json` from `self.config_path`.
        *   If the file exists and is valid JSON, it merges the loaded settings with the default settings. This ensures that if new settings are added to `default_config` in a newer app version, users with old config files still get values for the new keys. Loaded settings take precedence over defaults for existing keys.
        *   If the file doesn't exist or is corrupted, it returns a fresh copy of `self.default_config`.
        *   Includes error handling for file I/O and JSON parsing.
    *   `save_config(settings: dict)`:
        *   Writes the provided `settings` dictionary to `self.config_path` as a JSON file, typically with indentation for readability.
        *   Ensures the directory for the config file exists before writing.
        *   Includes error handling.

## Integration with the Application

1.  **Initialization:**
    *   An instance of `ConfigManager` is typically created early in the application's lifecycle, usually within `IntelliSubsApp.__init__()`.
    *   The loaded configuration dictionary is then stored in `IntelliSubsApp` (e.g., `self.app_config`).

2.  **Accessing Configuration:**
    *   **UI Layer (`intellisubs/ui/`):**
        *   UI components (e.g., in `MainWindow` or settings panels) read from `self.app.app_config` to display current settings (e.g., pre-fill API key fields, select current ASR model in a dropdown).
        *   When the user changes a setting in the UI, the corresponding value in `self.app.app_config` is updated.
    *   **Core Logic Layer (`intellisubs/core/`):**
        *   The `WorkflowManager` is initialized with the relevant parts of `self.app_config`.
        *   Core modules (like `WhisperService`, `LLMEnhancer`) receive their specific configurations (e.g., model name, API key) from the `WorkflowManager` or directly from the passed config dictionary.

3.  **Saving Configuration:**
    *   Configuration is typically saved:
        *   When the user explicitly clicks a "Save Settings" or "Apply" button in a settings dialog.
        *   Automatically when the application is closed gracefully (e.g., in `IntelliSubsApp.quit_app()`).
    *   The `IntelliSubsApp` would call `self.config_manager.save_config(self.app_config)`.

## Handling API Keys and Sensitive Information

*   API keys (e.g., for OpenAI) are stored as strings in `config.json`.
*   By default, these keys are stored in plain text within the JSON file.
*   **Security Implication:** The `config.json` file should be protected by operating system file permissions (as it's usually in the user's profile directory). Users should be advised about the sensitivity if they share their computer or configuration.
*   **No Encryption by Default (v1.1):** Implementing robust, user-friendly encryption for API keys in a local config file adds significant complexity (key management, master passwords, etc.) and is out of scope for the initial versions as per `DEVELOPMENT.md`. The focus is on clear local storage.
*   The UI should use masked input fields (e.g., password-style) when displaying or allowing input of API keys.

## Future Considerations

*   **Profile Management:** For users who might want different sets of configurations (e.g., one for speed, one for accuracy), a profile system could be built on top of `ConfigManager`.
*   **Configuration Schema Validation:** For very complex configurations, using a schema (like JSON Schema) to validate the `config.json` content could be beneficial.
*   **UI for all Settings:** Ensure all configurable options defined in `get_default_settings()` are exposed through the UI settings panel, where appropriate.

This configuration management approach provides a flexible and robust way to handle application settings for IntelliSubs.