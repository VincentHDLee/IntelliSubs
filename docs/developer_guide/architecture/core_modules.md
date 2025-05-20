# Core Modules Deep Dive

This document provides a more detailed look into the design and responsibilities of the key modules within the `intellisubs/core/` package. These modules form the backend logic of the IntelliSubs application.

*(Refer to [Architecture Overview](./overview.md) for the broader context.)*

## 1. `WorkflowManager` (`workflow_manager.py`)

*   **Responsibility:** Acts as the central orchestrator for the entire subtitle generation process. It takes high-level requests (e.g., "process this audio file and return SRT subtitles") and coordinates the necessary steps by calling other core services.
*   **Key Methods (Conceptual):**
    *   `__init__(config: dict)`: Initializes itself and all necessary sub-services (ASR, audio processor, text processors, formatters) based on the provided application configuration.
    *   `process_audio_to_subtitle_data(input_audio_path: str, target_format: str) -> tuple[str, Any]`:
        *   Manages temporary file handling.
        *   Calls `AudioProcessor` to prepare the audio.
        *   Calls the selected `ASRService` to get raw transcriptions.
        *   Passes ASR output through the text processing pipeline: `Normalizer`, `Punctuator`, (optional) `LLMEnhancer`, `SubtitleSegmenter`.
        *   Returns a structured representation of subtitle lines (e.g., a list of dictionaries with text, start, end) and a status message. This intermediate data is then passed to a formatter.
    *   `format_subtitle_data(subtitle_data: Any, target_format: str) -> str`:
        *   Takes the intermediate subtitle data (from `process_audio_to_subtitle_data`) and uses the appropriate `SubtitleFormatter` to convert it into the final string representation for the target file format.
    *   `update_config(new_config: dict)`: Allows dynamic updates to its configuration, potentially re-initializing sub-services if critical settings (like ASR model or LLM API key) change.
*   **Design Notes:**
    *   Aims to be stateless regarding individual processing jobs, relying on passed arguments and its configured services.
    *   Error handling and logging are critical within this manager to provide feedback to the UI or calling R`untime.

## 2. Audio Processing (`audio_processing/processor.py`)

*   **Class:** `AudioProcessor`
*   **Responsibility:** Handles all operations related to preparing audio for the ASR engine.
*   **Key Methods:**
    *   `preprocess_audio(input_path: str, output_path: str) -> str`: A high-level method that might chain several steps. If `input_path` is a video, it first calls `extract_audio_from_video`. Then, it calls `convert_to_standard_format`. Optionally, it might call `apply_noise_reduction`.
    *   `extract_audio_from_video(video_path: str, audio_output_path: str) -> str`: Uses `ffmpeg` (likely via `ffmpeg-python`) to extract the audio track from a video file and save it.
    *   `convert_to_standard_format(input_path: str, output_path: str) -> str`: Uses `ffmpeg` to convert the input audio to a format optimal for Whisper (e.g., 16kHz sample rate, mono channel, 16-bit WAV).
    *   `apply_noise_reduction(input_path: str, output_path: str) -> str`: (Optional) Uses a library like `noisereduce` to attempt to reduce background noise. This is a lower priority for AI-generated voice.
*   **Dependencies:** `ffmpeg-python`, `pydub` (for simpler manipulations if needed), `noisereduce`, `soundfile` (for reading/writing audio with `noisereduce`).

## 3. ASR Services (`asr_services/`)

*   **Base Class:** `BaseASRService` (in `base_asr.py`)
    *   **Responsibility:** Defines the abstract interface that all ASR service implementations must adhere to.
    *   **Key Abstract Methods:**
        *   `transcribe(audio_path: str) -> list`: Takes a path to a preprocessed audio file and returns a list of transcribed segments. Each segment should ideally be a dictionary or object containing `text`, `start_time`, and `end_time`.
*   **Implementation:** `WhisperService` (in `whisper_service.py`)
    *   **Responsibility:** Implements the `BaseASRService` interface using the `faster-whisper` library.
    *   **Initialization:** Takes parameters like `model_name` (e.g., "small", "medium"), `device` ("cpu", "cuda"), and `compute_type` ("float16", "int8", etc.).
    *   **`transcribe` Method:** Loads the specified Whisper model (if not already loaded) and performs transcription on the given audio file, specifically for Japanese (`language="ja"`). It processes the output from `faster-whisper` into the common segment format.
*   **Extensibility:** New ASR engines (e.g., a local ReazonSpeech model, or a cloud-based ASR) can be integrated by creating a new class that inherits from `BaseASRService` and implementing the `transcribe` method.

## 4. Text Processing (`text_processing/`)

This package contains several modules that work sequentially to refine the raw ASR output.

*   **`ASRNormalizer` (`normalizer.py`)**
    *   **Responsibility:** Performs initial cleanup and normalization of ASR text.
    *   **Key Methods:**
        *   `load_custom_dictionary(file_path: str)`: Loads find-and-replace rules from a user-provided file.
        *   `normalize_text_segments(segments: list) -> list`: Applies custom dictionary rules, removes common ASR disfluencies (e.g., "えーと"), and potentially merges overly fragmented short segments based on timing and length.
*   **`Punctuator` (`punctuator.py`)**
    *   **Responsibility:** Adds or corrects punctuation in the text segments.
    *   **Key Methods:**
        *   `add_punctuation(text_segments: list) -> list`: For Japanese, this involves intelligently adding `。`, `、`, `？`, `！`. Initial versions might use rule-based approaches (e.g., based on pause durations from ASR timestamps, common sentence-ending particles). Future versions could integrate a dedicated punctuation model or leverage LLM for this.
*   **`LLMEnhancer` (`llm_enhancer.py`)**
    *   **Responsibility:** (Optional) Uses a Large Language Model to further refine text for grammar, style, clarity, and more sophisticated punctuation.
    *   **Key Methods:**
        *   `enhance_text_segments(text_segments: list) -> list`: Iterates through text segments, constructs appropriate prompts for the LLM (e.g., asking it to refine Japanese subtitle text), calls the LLM API, and replaces the original text with the LLM's output.
    *   **Dependencies:** `openai` library. Requires API key and internet access for cloud LLMs.
*   **`SubtitleSegmenter` (`segmenter.py`)**
    *   **Responsibility:** Takes the processed (and potentially punctuated/LLM-enhanced) text segments and divides them into lines suitable for display as subtitles.
    *   **Key Methods:**
        *   `segment_into_subtitle_lines(punctuated_text_segments: list) -> list`: Considers factors like maximum characters per line (configurable, accounting for Japanese character width), maximum duration per subtitle entry, and natural break points (e.g., after punctuation). It might split a single long ASR segment into multiple subtitle entries or add line breaks (`\n`) within a single entry's text.

## 5. Subtitle Formats (`subtitle_formats/`)

*   **Base Class:** `BaseSubtitleFormatter` (in `base_formatter.py`)
    *   **Responsibility:** Defines an abstract interface for converting a list of processed subtitle entries into a specific file format string.
    *   **Key Abstract Methods:**
        *   `format_subtitles(subtitle_entries: list) -> str`.
    *   **Helper Methods:** `save_subtitles` (writes formatted string to file with specified encoding).
*   **Implementations:**
    *   **`SRTFormatter` (`srt_formatter.py`):** Outputs `.srt` format.
    *   **`LRCFormatter` (`lrc_formatter.py`):** Outputs `.lrc` format.
    *   **`ASSFormatter` (`ass_formatter.py`):** Outputs basic `.ass` format.
*   **Design:** Each formatter is responsible for adhering to the syntax of its target format. Timecode conversion utilities are often included or shared.
*   **Dependencies:** `pysrt` could be used as an alternative or helper for SRT, but manual formatting is also straightforward for basic cases.

---

Understanding these core modules and their interactions is key to developing and extending IntelliSubs. Each module is designed to be testable independently.