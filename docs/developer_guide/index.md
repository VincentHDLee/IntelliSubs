# IntelliSubs Developer Guide

Welcome to the Developer Guide for 智字幕 (IntelliSubs)!

This guide is intended for developers who want to understand the project's architecture, contribute to its development, or build upon its codebase.

## Contents

1.  **[Setting Up Development Environment](./setup_env.md)**
    *   Prerequisites (Python version, Git, etc.)
    *   Cloning the Repository
    *   Creating and Activating a Virtual Environment
    *   Installing Dependencies
    *   Recommended IDEs and Extensions (e.g., VS Code with Python extension)
    *   Running the Application in Development Mode
    *   Running Tests

2.  **[Project Structure Overview](../PROJECT_STRUCTURE.md)**
    *   (Link to the existing `PROJECT_STRUCTURE.md` in the root for a detailed breakdown of directories and files.)

3.  **[Coding Standards](./coding_standards.md)**
    *   Code Formatting (e.g., Black, autopep8)
    *   Linting (e.g., Flake8, Pylint)
    *   Naming Conventions
    *   Docstrings and Commenting Style (e.g., Google Style, reStructuredText for Sphinx)
    *   Type Hinting (PEP 484)
    *   Git Commit Message Conventions (e.g., Conventional Commits)

4.  **Architecture Deep Dive**
    *   **[Overview](./architecture/overview.md)**
        *   High-level component diagram and data flow.
    *   **[Core Modules](./architecture/core_modules.md)**
        *   Detailed explanation of modules within `intellisubs/core/`:
            *   `asr_services` (Whisper integration)
            *   `audio_processing`
            *   `text_processing` (Normalization, Punctuation, Segmentation, LLM)
            *   `subtitle_formats`
            *   `workflow_manager`
    *   **[UI Design](./architecture/ui_design.md)**
        *   Overview of the CustomTkinter UI structure (`intellisubs/ui/`).
        *   Key views, widgets, and event handling.
        *   (If applicable) Model-View-Controller (MVC) or Model-View-ViewModel (MVVM) patterns used.
    *   **[Configuration Management](./architecture/config_management.md)**
        *   How `ConfigManager` works, default configurations, and storage.
    *   **[Logging Strategy](./architecture/logging_strategy.md)**
        *   How `logger_setup` is used, log levels, and log file locations.

5.  **Development Guides (How-To's)**
    *   **[Adding a New ASR Engine](./guides/adding_new_asr_engine.md)** (Placeholder)
        *   Steps to integrate a different ASR provider or model.
    *   **[Extending Subtitle Formats](./guides/extending_subtitle_formats.md)** (Placeholder)
        *   How to add support for a new subtitle export format.
    *   **[Modifying the UI](./guides/modifying_the_ui.md)** (Placeholder)
        *   Tips for working with CustomTkinter and the existing UI structure.

6.  **[Testing Strategy](../DEVELOPMENT.md#9-测试策略概要)**
    *   (Link to the testing strategy section in `DEVELOPMENT.md`)
    *   Details on running unit tests, integration tests, and (if applicable) UI tests.

7.  **[Building and Packaging](./build_and_packaging.md)**
    *   How to use PyInstaller or Nuitka (via `scripts/build_app.py` or manually) to create distributable versions for Windows.
    *   Handling dependencies and assets during packaging.

8.  **[Contributing to IntelliSubs](../../CONTRIBUTING.md)**
    *   (Link to the main `CONTRIBUTING.md` file for guidelines on pull requests, issue tracking, etc.)

---

This guide aims to provide all the necessary information for developers to effectively work on IntelliSubs. If you find any part unclear or missing, please feel free to contribute to this documentation!