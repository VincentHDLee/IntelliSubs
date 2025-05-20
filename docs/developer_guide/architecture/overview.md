# Architecture Overview

This document provides a high-level overview of the 智字幕 (IntelliSubs) application architecture. The goal is to create a modular, maintainable, and extensible system.

*(Refer to the System Architecture diagram in [DEVELOPMENT.md](../../../DEVELOPMENT.md#5-系统架构-高层次) for a visual representation. This section will elaborate on it.)*

## Core Principles

*   **Modularity:** The application is divided into distinct modules with well-defined responsibilities and interfaces. This promotes separation of concerns and makes the system easier to understand, test, and modify.
*   **Separation of Concerns:** UI logic is kept separate from core processing logic. Business logic (subtitle generation workflow) is distinct from low-level ASR or text manipulation utilities.
*   **Configurability:** Key aspects of the application (ASR models, LLM settings, paths) are configurable to adapt to user needs and different environments.
*   **Extensibility:** The architecture is designed to allow for future enhancements, such as adding new ASR engines, subtitle formats, or LLM providers.

## Main Components

The application can be broadly divided into the following main components, as reflected in the [project structure](../../../PROJECT_STRUCTURE.md):

1.  **`intellisubs/ui/` (User Interface Layer)**
    *   **Responsibility:** Handles all user interaction, displays information, and captures user input.
    *   **Technology:** Built using `CustomTkinter` for a modern Tkinter look and feel on Windows.
    *   **Key Parts:**
        *   `app.py`: The main application class (`IntelliSubsApp`), which initializes the main window and manages global application state.
        *   `views/main_window.py`: Defines the primary user interface layout, including file selection, controls, preview area, and export options.
        *   `widgets/`: Contains any custom UI widgets developed for the application (though many standard CustomTkinter widgets will be used directly).
    *   **Interaction:** Communicates with the Core Logic Layer (primarily via the `WorkflowManager`) to trigger actions (like starting subtitle generation) and display results. It also interacts with the `ConfigManager` to load and save UI-related settings.

2.  **`intellisubs/core/` (Core Logic / Backend Layer)**
    *   **Responsibility:** Implements all the business logic related to subtitle generation. This layer is designed to be UI-agnostic, meaning it could potentially be driven by other interfaces (e.g., a CLI) in the future.
    *   **Key Sub-modules:**
        *   **`workflow_manager.py`:** Orchestrates the entire subtitle generation pipeline. It coordinates calls to various services (audio processing, ASR, text processing, formatting). This is the primary entry point for the UI to interact with the core logic.
        *   **`audio_processing/processor.py`:** Handles tasks like audio extraction from video, format conversion (e.g., to 16kHz mono WAV suitable for ASR), and optional noise reduction.
        *   **`asr_services/`:** Contains implementations for different ASR engines.
            *   `base_asr.py`: Defines an abstract base class for ASR services.
            *   `whisper_service.py`: Implements ASR using `faster-whisper`.
        *   **`text_processing/`:** A suite of modules for refining the raw ASR output:
            *   `normalizer.py`: Applies custom dictionary replacements and basic text cleanup.
            *   `punctuator.py`: Adds or corrects punctuation (initially rule-based, potentially LLM-assisted).
            *   `segmenter.py`: Breaks down processed text into appropriately timed and sized subtitle lines.
            *   `llm_enhancer.py`: (Optional) Uses an LLM for advanced text refinement.
        *   **`subtitle_formats/`:** Handles formatting the processed subtitle lines into standard file formats (SRT, LRC, ASS).
            *   `base_formatter.py`: Abstract base class for formatters.
            *   `srt_formatter.py`, `lrc_formatter.py`, `ass_formatter.py`: Specific implementations.

3.  **`intellisubs/utils/` (Utilities Layer)**
    *   **Responsibility:** Provides common, reusable utility functions and classes used across the application.
    *   **Key Parts:**
        *   `config_manager.py`: Manages loading and saving application settings from/to a configuration file (e.g., `config.json`).
        *   `logger_setup.py`: Configures application-wide logging.
        *   `file_handler.py`: Provides helper functions for file system operations (e.g., ensuring directories exist, path manipulation).

4.  **Configuration Files (e.g., `config.json`)**
    *   Stores user preferences and application settings persistently.
    *   Managed by `ConfigManager`.

5.  **Resource Files (`resources/`)**
    *   Contains static assets needed by the application, such as:
        *   Default ASR models (if bundled or downloaded here).
        *   Sample custom dictionaries.
        *   Application icons.
        *   Internationalization files (if UI is localized in the future).

## High-Level Data Flow (Example: Generating Subtitles)

1.  **User Interaction (UI):** User selects an audio/video file and clicks "Start Generation" in `MainWindow`.
2.  **Request to Core (UI -> Core):** `MainWindow` calls a method on `IntelliSubsApp`, which in turn invokes the `WorkflowManager`'s main processing method, passing the file path and current settings.
3.  **Audio Preprocessing (Core):** `WorkflowManager` uses `AudioProcessor` to convert the input file into a standard audio format suitable for ASR.
4.  **ASR Transcription (Core):** `WorkflowManager` passes the processed audio to the selected `ASRService` (e.g., `WhisperService`), which returns raw text segments with timestamps.
5.  **Text Processing Pipeline (Core):** `WorkflowManager` pipes the ASR segments through:
    *   `ASRNormalizer` (custom dictionary, basic cleanup).
    *   `Punctuator` (punctuation addition).
    *   (Optional) `LLMEnhancer` (LLM-based refinement).
    *   `SubtitleSegmenter` (breaks text into subtitle lines with appropriate timings).
6.  **Result Display (Core -> UI):** The `WorkflowManager` returns the processed subtitle lines (or an error status) to the UI. `MainWindow` updates the preview area.
7.  **User Export Request (UI):** User selects an export format (e.g., SRT) and clicks "Export".
8.  **Subtitle Formatting (UI -> Core -> UI):** `MainWindow` requests formatting. `WorkflowManager` (or `IntelliSubsApp` delegating to it) uses the appropriate `SubtitleFormatter` (e.g., `SRTFormatter`) to convert the subtitle lines into the target format string. This string is returned.
9.  **File Saving (UI):** `MainWindow` prompts the user for a save location and writes the formatted string to a file.

This modular approach allows individual components to be developed, tested, and improved independently. For example, a new ASR engine could be added by implementing the `BaseASRService` interface without requiring major changes to the UI or workflow orchestration, as long as the interface contract is met.