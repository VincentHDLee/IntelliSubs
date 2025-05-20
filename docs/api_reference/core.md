# Core API Reference (Conceptual)

This section is intended to house automatically generated or manually curated API documentation for the core public interfaces of the 智字幕 (IntelliSubs) application, primarily focusing on modules within `intellisubs.core`.

**Note:** For the initial versions, detailed API reference generation might be a lower priority compared to functional code and user/developer guides. However, well-documented code (using docstrings) is essential from the start, as this forms the basis for any future auto-generated API documentation.

## Potential Tooling

If/when formal API documentation is generated, tools like [Sphinx](https://www.sphinx-doc.org/) with the `sphinx.ext.autodoc` and `sphinx.ext.napoleon` (for Google/NumPy style docstrings) extensions would be suitable.

## Key Public Interfaces (Examples of what might be documented here)

This is a conceptual list of classes and methods that would be prime candidates for API documentation if IntelliSubs were to be used as a library or if developers needed to deeply integrate with its core components.

### 1. `intellisubs.core.workflow_manager.WorkflowManager`

*   `WorkflowManager(config: dict = None)`
    *   `process_audio_to_subtitle_data(input_audio_path: str, target_format: str) -> tuple[str, Any]`
    *   `format_subtitle_data(subtitle_data: Any, target_format: str) -> str`
    *   `update_config(new_config: dict)`

### 2. `intellisubs.core.asr_services.base_asr.BaseASRService` (Abstract Base Class)

*   `transcribe(audio_path: str) -> list` (Abstract method)

### 3. `intellisubs.core.asr_services.whisper_service.WhisperService`

*   `WhisperService(model_name: str = "small", device: str = "cpu", compute_type: str = "float32")`
*   `transcribe(audio_path: str) -> list`

### 4. `intellisubs.core.audio_processing.processor.AudioProcessor`

*   `AudioProcessor(target_sample_rate=16000, ...)`
*   `preprocess_audio(input_path: str, output_path: str) -> str`
*   `extract_audio_from_video(video_path: str, audio_output_path: str) -> str`
*   `convert_to_standard_format(input_path: str, output_path: str) -> str`
*   `apply_noise_reduction(input_path: str, output_path: str) -> str`

### 5. `intellisubs.core.text_processing.normalizer.ASRNormalizer`

*   `ASRNormalizer(custom_dictionary_path: Optional[str] = None)`
*   `load_custom_dictionary(file_path: str)`
*   `normalize_text_segments(segments: list) -> list`

### 6. `intellisubs.core.text_processing.punctuator.Punctuator`

*   `Punctuator(language: str = "ja")`
*   `add_punctuation(text_segments: list) -> list`

### 7. `intellisubs.core.text_processing.llm_enhancer.LLMEnhancer`

*   `LLMEnhancer(api_key: Optional[str] = None, model_name: str = "gpt-3.5-turbo", ...)`
*   `enhance_text_segments(text_segments: list) -> list`

### 8. `intellisubs.core.text_processing.segmenter.SubtitleSegmenter`

*   `SubtitleSegmenter(max_chars_per_line: int = 25, ...)`
*   `segment_into_subtitle_lines(punctuated_text_segments: list) -> list`

### 9. `intellisubs.core.subtitle_formats.base_formatter.BaseSubtitleFormatter` (Abstract Base Class)

*   `format_subtitles(subtitle_entries: list) -> str` (Abstract method)
*   `save_subtitles(subtitle_entries: list, output_path: str, encoding: str = "utf-8")`

### 10. Specific Formatters (e.g., `SRTFormatter`, `LRCFormatter`, `ASSFormatter`)

*   Constructors (if any specific options).
*   `format_subtitles(subtitle_entries: list) -> str`

---

The actual content of an API reference would be much more detailed, including parameter types, return types, exceptions raised, and explanations derived from comprehensive docstrings within the source code. This file serves as a placeholder for that eventual content.