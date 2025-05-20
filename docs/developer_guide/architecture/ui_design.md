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
    *   **Role:** The primary view of the application, a frame that sits within `IntelliSubsApp`. It contains all the main interactive elements for subtitle generation.
    *   **Layout (Conceptual, using Grids):**
        *   **Controls Frame (Top):**
            *   File selection (label, entry field for path, "Select File" button).
            *   "Start Generation" button.
            *   (Potentially) Basic settings like ASR model dropdown, CPU/GPU toggle, if not in a separate settings panel.
        *   **Results Frame (Middle/Main Area):**
            *   **Preview Textbox:** A large `CTkTextbox` to display status messages during processing and the generated subtitle text afterward. Should be scrollable and read-only for the user.
            *   **Export Controls (Below Preview):**
                *   Dropdown (`CTkOptionMenu`) to select export format (SRT, LRC, ASS).
                *   "Export Subtitles" button.
        *   **(Future/Optional) Settings Sidebar/Panel:** A dedicated frame for more detailed settings (LLM options, custom dictionary path, advanced ASR parameters, UI theme). This keeps the main workflow area cleaner.
    *   **Event Handling:**
        *   Button clicks (`command` callbacks) trigger actions.
        *   File selection updates the path entry and enables/disables the start button.
        *   Start button click initiates the subtitle generation process (delegating to `app.workflow_manager`).
        *   Export button click initiates the file saving process.
    *   **Updating UI based on Core Logic:**
        *   When processing starts, UI elements are disabled/updated to reflect the busy state.
        *   Status messages from `WorkflowManager` are displayed in the preview box or a status bar.
        *   When results are ready, they are populated into the preview box, and export options are enabled.

3.  **`widgets/` (Custom Widgets Package)**
    *   **Role:** To house any reusable custom UI components built on top of CustomTkinter or standard Tkinter, if needed.
    *   **Examples (Hypothetical):**
        *   `file_dialogs.py`: Could contain wrapped versions of `tkinter.filedialog` if specific pre/post-processing or theming for dialogs is required (though often direct use is fine).
        *   `Tooltip.py`: If a custom tooltip implementation is needed.
        *   `SettingsPanel.py`: If the settings area becomes complex, it could be its own custom widget/frame.
    *   Currently, most functionality might be achievable with standard CustomTkinter widgets directly within `MainWindow`.

4.  **`assets/` (UI Assets Package)**
    *   **Role:** Stores static assets for the UI.
    *   `icons/`: For any `.ico` or `.png` files used for application icon, button icons, etc. CustomTkinter has some built-in image handling capabilities.

## Event Handling and Threading

*   **Main UI Thread:** All Tkinter/CustomTkinter operations **must** occur in the main thread.
*   **Background Threads for Long Tasks:**
    *   Any time-consuming operations (ASR, LLM calls, extensive file I/O) initiated by UI actions (e.g., "Start Generation" button) **must** be run in a separate worker thread (using Python's `threading` module).
    *   This prevents the UI from freezing and becoming unresponsive.
    *   **Communicating Back to UI:** The worker thread cannot directly update UI widgets. It must use a thread-safe mechanism to send results or progress updates back to the main UI thread. Common methods:
        *   Using a `queue.Queue` to pass messages/data from the worker thread to the main thread, where the main thread periodically checks the queue (e.g., using `after()` method).
        *   Using `master.after(0, callback)` or widget-specific `after` calls to schedule a function to run in the main event loop.
        *   CustomTkinter widgets might have their own mechanisms or be compatible with standard Tkinter approaches.
    *   **Example Flow:**
        1.  User clicks "Start".
        2.  `MainWindow` method disables relevant UI, shows "Processing..." message.
        3.  `MainWindow` method starts a new `Thread` targeting a function in `app.workflow_manager`.
        4.  Worker thread performs processing.
        5.  Worker thread puts results (or progress updates) into a shared queue or uses a callback scheduled with `master.after()`.
        6.  Main UI thread (via `after()` loop or queue check) picks up the result and updates the `CTkTextbox`, enables UI elements.

## Configuration and Theming

*   `IntelliSubsApp` will load initial UI settings (like theme, appearance mode) from `ConfigManager`.
*   CustomTkinter's `set_appearance_mode()` and `set_default_color_theme()` will be used.
*   Users should be able to change these settings via a settings panel, and these changes should be saved back via `ConfigManager`.

## Future UI Enhancements (Considerations from `DEVELOPMENT.md`)

*   **More detailed preview:** Instead of just text, perhaps a scrolling preview synchronized with a simplified audio waveform or a timestamped list.
*   **Basic subtitle editing:** Allow minor text corrections directly in a preview/edit pane (this is a significant feature increase).
*   **Japanese UI Localization:** Abstracting UI strings for easier translation.

This UI architecture aims for a balance between simplicity of implementation (leveraging CustomTkinter) and the responsiveness/features expected of a modern desktop application.