# How-To: Adding a New ASR Engine

This guide outlines the general steps and considerations for integrating a new Automatic Speech Recognition (ASR) engine into the 智字幕 (IntelliSubs) application.

The system is designed with an abstraction layer for ASR services, defined by `intellisubs.core.asr_services.base_asr.BaseASRService`.

## Prerequisites

*   Familiarity with the chosen ASR engine's SDK or API.
*   Understanding of the `BaseASRService` interface in IntelliSubs.
*   Development environment set up as per [Setup Development Environment](../setup_env.md).

## Steps

1.  **Create a New ASR Service Class:**
    *   In the `intellisubs/core/asr_services/` directory, create a new Python file for your ASR engine (e.g., `my_new_asr_service.py`).
    *   Define a new class that inherits from `BaseASRService`:
        ```python
        # intellisubs/core/asr_services/my_new_asr_service.py
        from .base_asr import BaseASRService
        # Import any SDKs or libraries needed for your new ASR engine
        # import my_new_asr_sdk 

        class MyNewASRService(BaseASRService):
            def __init__(self, model_path: str = None, api_key: str = None, language: str = "ja", **kwargs):
                """
                Initialize your new ASR service.
                Store necessary configurations like model paths, API keys, language.
                """
                self.model_path = model_path
                self.api_key = api_key
                self.language = language
                # self.client = my_new_asr_sdk.Client(api_key=api_key) # Example
                # self.model = my_new_asr_sdk.load_model(model_path) # Example
                print(f"MyNewASRService initialized for language: {language}")

            def transcribe(self, audio_path: str) -> list:
                """
                Transcribes the given audio file using your new ASR engine.

                Args:
                    audio_path (str): Path to the preprocessed audio file (e.g., 16kHz mono WAV).

                Returns:
                    list: A list of transcribed segments. Each segment must be a dictionary
                          containing at least 'text', 'start' (in seconds), and 'end' (in seconds).
                          Example: [{'text': 'こんにちは', 'start': 0.5, 'end': 1.2}, ...]
                """
                transcribed_segments = []
                
                # 1. Load/prepare your ASR model if it's not already loaded.
                # 2. Call your ASR engine's transcription function with audio_path.
                #    Ensure the audio format matches what your engine expects.
                #    raw_results = self.model.process(audio_path) # Example call

                # 3. Convert the raw results from your ASR engine into the
                #    standardized segment format required by IntelliSubs:
                #    A list of dicts: [{'text': str, 'start': float_seconds, 'end': float_seconds}, ...]

                # Example placeholder conversion:
                # for raw_segment in raw_results.get_segments():
                #     transcribed_segments.append({
                #         "text": raw_segment.get_text(),
                #         "start": raw_segment.get_start_time_seconds(),
                #         "end": raw_segment.get_end_time_seconds()
                #     })
                
                # Placeholder for actual implementation:
                print(f"MyNewASRService: Transcribing {audio_path} (Placeholder)")
                transcribed_segments.append({"text": "新しいASRからのテキスト", "start": 1.0, "end": 3.0})
                transcribed_segments.append({"text": "これはテストです。", "start": 3.5, "end": 5.0})

                return transcribed_segments
        ```

2.  **Update `WorkflowManager` (and Configuration):**
    *   The `WorkflowManager` (`intellisubs/core/workflow_manager.py`) needs to be aware of this new ASR service.
    *   **Configuration (`ConfigManager`):**
        *   Add new configuration options to `intellisubs/utils/config_manager.py` in `get_default_settings()` if your new ASR service requires specific settings (e.g., `my_new_asr_model_name`, `my_new_asr_api_url`).
        *   Consider adding an `asr_engine_type` setting (e.g., "whisper", "my_new_asr") to allow users to choose.
    *   **`WorkflowManager.__init__`:**
        *   Modify the `WorkflowManager`'s constructor to instantiate your new ASR service based on the configuration.
            ```python
            # In WorkflowManager.__init__
            # from .asr_services.my_new_asr_service import MyNewASRService # Add import

            # ...
            # current_asr_engine_type = self.config.get("asr_engine_type", "whisper")
            # if current_asr_engine_type == "my_new_asr":
            #     self.asr_service = MyNewASRService(
            #         model_path=self.config.get("my_new_asr_model_path"),
            #         api_key=self.config.get("my_new_asr_api_key"),
            #         language=self.config.get("language", "ja")
            #     )
            # elif current_asr_engine_type == "whisper":
            #     self.asr_service = WhisperService(...) # Existing Whisper init
            # else:
            #     # Fallback or error
            #     self.asr_service = WhisperService(...)
            ```

3.  **Update UI (Settings Panel):**
    *   If users need to select this new ASR engine or configure its specific settings, the UI (`intellisubs/ui/views/main_window.py` or a dedicated settings panel) must be updated.
    *   Add new widgets (dropdowns, input fields) for these settings.
    *   Ensure these UI settings are saved to and loaded from the `config.json` via `ConfigManager`.

4.  **Audio Preprocessing Considerations:**
    *   The `AudioProcessor` currently standardizes audio to a format suitable for Whisper (e.g., 16kHz mono WAV).
    *   Verify if your new ASR engine has different input audio requirements. If so, you might need to:
        *   Modify `AudioProcessor` to handle different output formats based on the selected ASR engine.
        *   Or, ensure your new ASR service class can handle the standard output of `AudioProcessor` and perform any final necessary conversions internally.

5.  **Add Dependencies:**
    *   If your new ASR engine requires specific Python packages or external libraries, add them to `requirements.txt`.
    *   Document any system-level dependencies (e.g., specific DLLs, external software) in `docs/developer_guide/setup_env.md` or a dedicated section for the new ASR engine.

6.  **Documentation:**
    *   Update `DEVELOPMENT.md` if this significantly changes the ASR strategy.
    *   Update the user manual (`docs/user_manual/features/asr_settings.md`) to explain how to use and configure the new ASR engine.
    *   Update this developer guide with any specific notes about your new ASR engine.

7.  **Testing:**
    *   Create new unit tests for your `MyNewASRService` class in the `tests/core/asr_services/` directory (e.g., `test_my_new_asr_service.py`).
    *   Mock external API calls or SDK interactions if necessary for isolated testing.
    *   Perform integration tests to ensure it works correctly within the `WorkflowManager` and with the UI.

## Example: Output Segment Format

The `transcribe` method of your new ASR service **must** return a list of dictionaries. Each dictionary represents a single, continuous speech segment and should have the following keys:

*   `'text'` (str): The transcribed text for that segment.
*   `'start'` (float): The start time of the segment in seconds from the beginning of the audio.
*   `'end'` (float): The end time of the segment in seconds from the beginning of the audio.

Example:
```python
[
    {'text': '最初のセグメントです。', 'start': 0.52, 'end': 2.88},
    {'text': 'そして、これは次の部分です。', 'start': 3.1, 'end': 5.0}
]
```
The rest of the IntelliSubs pipeline (text processing, subtitle formatting) relies on this format.

---

By following these steps and adhering to the `BaseASRService` interface, you can integrate new ASR capabilities into IntelliSubs in a modular way.