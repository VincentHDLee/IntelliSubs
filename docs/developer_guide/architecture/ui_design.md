# UI Design and Architecture

This document details the User Interface (UI) design principles and architectural approach for 智字幕 (IntelliSubs), focusing on the `intellisubs/ui/` package which primarily uses the `CustomTkinter` library.

*(Refer to [Architecture Overview](./overview.md) for how the UI fits into the larger system.)*

## Guiding Principles for UI

*   **Simplicity and Ease of Use:** The primary users are content creators (小编) who may not be highly technical. The UI should be intuitive, with a minimal learning curve.
*   **Clarity:** All options, buttons, and status messages should be clearly labeled and easy to understand. UI language is initially Chinese, with potential for Japanese localization later.
*   **Responsiveness:** The UI should remain responsive even during long processing tasks. This implies that compute-intensive operations (like ASR, LLM calls) must be run in separate threads to avoid freezing the main UI thread.
*   **Feedback:** Provide clear feedback to the user about the application's state (e.g., "processing file...", "generating subtitles...", "error occurred...", "successfully exported").
*   **Windows Native Feel (via CustomTkinter):** While Tkinter is cross-platform, CustomTkinter helps give it a more modern and Windows-like appearance.
*   **Minimal Configuration by Default:** Sensible defaults should be provided for all settings, allowing users to get started quickly. Advanced options should be available but not overwhelming.

## UI Technology

*   **Main Library:** [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
    *   Chosen for its modern theming capabilities on top of Python's built-in Tkinter, ease of use for desktop applications, and good integration with Python.
    *   Allows for light/dark mode and theming.
*   **Standard Tkinter Elements:** Core Tkinter dialogs (like `filedialog`) will be used where CustomTkinter doesn't provide a direct replacement or when standard dialogs are sufficient.

## Key UI Components and Structure (`intellisubs/ui/`)

The UI has been refactored for better modularity and maintainability, with `MainWindow` acting as a coordinator for specialized sub-panels.

1.  **`app.py` - `IntelliSubsApp(ctk.CTk)`**
    *   **Role:** The main application class, inheriting from `customtkinter.CTk`. It acts as the root window and a central point for managing the application's lifecycle and global state.
    *   **Responsibilities:**
        *   Initializes the main application window (title, size, appearance mode, color theme).
        *   Sets up global resources like logging (via `logger_setup`) and configuration management (via `ConfigManager`).
        *   Instantiates the `WorkflowManager` from the core layer, passing the application config.
        *   Instantiates and displays the `MainWindow` frame.
        *   Handles application-wide events (e.g., window closing, global shortcuts).
        *   Manages saving configuration on exit.

2.  **`views/main_window.py` - `MainWindow(ctk.CTkFrame)`**
    *   **Role:** Acts as the primary view container and **coordinator** for various UI sub-panels. It orchestrates the interaction between these panels and the application's core logic (e.g., `WorkflowManager`).
    *   **Structure:**
        *   Instantiates and arranges the main UI panels: `TopControlsPanel`, `SettingsPanel`, and `ResultsPanel`.
        *   Manages a display area for the list of selected files.
    *   **Responsibilities:**
        *   Passes necessary dependencies (config, logger, workflow_manager, app reference) to the sub-panels.
        *   Defines and provides callbacks to sub-panels for them to trigger application-level actions (e.g., starting the subtitle generation process, updating configuration).
        *   Handles communication and data flow between panels if necessary (e.g., file selection in `TopControlsPanel` updating a list view managed by `MainWindow` and potentially affecting `ResultsPanel`).
        *   Initiates core processing tasks (like subtitle generation) in response to events from sub-panels, often by delegating to `WorkflowManager`.
        *   Manages global UI state updates that span across multiple panels (e.g., overall application status).

3.  **`views/main_window_components/` (Sub-Panel Modules)**
    This directory houses the refactored UI components, each a `ctk.CTkFrame` subclass responsible for a specific part of the main window's functionality.

    *   **`top_controls_panel.py` - `TopControlsPanel(ctk.CTkFrame)`**
        *   **Role:** Manages the top section of the UI.
        *   **Responsibilities:**
            *   Handles file selection (single or multiple) via a browse button and displays the selection status.
            *   Manages output directory selection.
            *   Contains the "Start Generation" button.
            *   Communicates file selections and start requests to `MainWindow` via callbacks.
            *   Approximate lines of code: ~112.

    *   **`settings_panel.py` - `SettingsPanel(ctk.CTkFrame)`**
        *   **Role:** Manages all user-configurable settings through a tabbed interface.
        *   **Responsibilities:**
            *   Provides UI elements (dropdowns, checkboxes, entry fields) for "Main Settings" (ASR model, processing device, language, custom dictionary path).
            *   Provides UI elements for "AI & Advanced Settings" (LLM enablement, LLM API key/URL/model, timeline adjustments).
            *   Loads initial settings from `config` and updates `config` via a callback to `MainWindow` when settings are changed by the user.
            *   Manages the visibility of LLM-specific options based on the "Enable LLM" checkbox.
            *   Approximate lines of code: ~192.

    *   **`results_panel.py` - `ResultsPanel(ctk.CTkFrame)`**
        *   **Role:** Manages the display of processing results, subtitle preview, and export functionalities.
        *   **Responsibilities:**
            *   Displays a list of processed files with their status (success/error).
            *   Provides a "Preview" button for each successful entry to load its subtitles into the main preview textbox.
            *   Manages the main `CTkTextbox` for subtitle preview, allowing text editing.
            *   Includes an "Apply Changes" button to save edits made in the preview textbox back to the internal data structures (via `WorkflowManager`).
            *   Provides controls for selecting subtitle export format (SRT, LRC, ASS, TXT).
            *   Includes "Export Current Preview" and "Export All Successful" buttons.
            *   Communicates export requests to `MainWindow` (which then might involve `WorkflowManager`).
            *   Approximate lines of code: ~196.

4.  **`widgets/` (Custom Widgets Package)**
    *   **Role:** To house any reusable custom UI components built on top of CustomTkinter or standard Tkinter, if specific UI elements are needed across different panels or for more complex interactions not covered by standard widgets.
    *   **Examples:** `file_dialogs.py` (if custom dialog wrappers are needed, though standard dialogs are often used directly by panels).

5.  **`assets/` (UI Assets Package)**
    *   **Role:** Stores static assets for the UI.
    *   `icons/`: For any `.ico` or `.png` files used for application icon, button icons, etc.

## Event Handling and Threading

*   **Main UI Thread:** All Tkinter/CustomTkinter operations **must** occur in the main thread.
*   **Background Threads for Long Tasks:**
    *   Any time-consuming operations (ASR, LLM calls, extensive file I/O) initiated by UI actions (e.g., "Start Generation" button) **must** be run in a separate worker thread (using Python's `threading` module).
    *   This prevents the UI from freezing and becoming unresponsive.
    *   **Communicating Back to UI:** The worker thread cannot directly update UI widgets. It must use a thread-safe mechanism to send results or progress updates back to the main UI thread. Common methods:
        *   Using a `queue.Queue` to pass messages/data from the worker thread to the main thread, where the main thread periodically checks the queue (e.g., using `after()` method).
        *   Using `master.after(0, callback)` or widget-specific `after` calls to schedule a function to run in the main event loop.
        *   CustomTkinter widgets might have their own mechanisms or be compatible with standard Tkinter approaches.
    *   **Example Flow (Post-Refactor):**
        1.  User selects files via `TopControlsPanel`. `TopControlsPanel` informs `MainWindow`.
        2.  `MainWindow` updates its internal list of selected files and potentially a shared file list display.
        3.  User clicks "Start" in `TopControlsPanel`.
        4.  `TopControlsPanel` calls the `start_processing_callback` provided by `MainWindow`.
        5.  `MainWindow`'s `start_processing` method:
            *   Retrieves current settings from `SettingsPanel`.
            *   Disables relevant UI elements across panels (or signals panels to disable themselves).
            *   Shows "Processing..." message (e.g., in `ResultsPanel` or a global status bar).
            *   Starts a new `Thread` targeting a function in `app.workflow_manager` (passing file paths and settings).
        6.  Worker thread in `WorkflowManager` performs processing.
        7.  Worker thread uses `app.after()` to schedule UI updates on the main thread. These updates might:
            *   Call methods in `ResultsPanel` to add entries to the results list.
            *   Call methods in `ResultsPanel` to populate the preview textbox for the first/selected successful result.
        8.  `MainWindow` (or `TopControlsPanel` itself) re-enables UI elements after processing is complete.

## Configuration and Theming

*   `IntelliSubsApp` will load initial UI settings (like theme, appearance mode) from `ConfigManager`.
*   CustomTkinter's `set_appearance_mode()` and `set_default_color_theme()` will be used.
*   Users should be able to change these settings via a settings panel, and these changes should be saved back via `ConfigManager`.

## Future UI Enhancements (Considerations from `DEVELOPMENT.md`)

*   **More detailed preview:** Instead of just text, perhaps a scrolling preview synchronized with a simplified audio waveform or a timestamped list.
*   **Basic subtitle editing:** Allow minor text corrections directly in the preview/edit pane within `ResultsPanel`. (Direct text editing implemented, D1I0 - Pending Test).
*   **Japanese UI Localization:** Abstracting UI strings for easier translation.

This UI architecture aims for a balance between simplicity of implementation (leveraging CustomTkinter) and the responsiveness/features expected of a modern desktop application.