# How-To: Modifying the UI

This guide provides tips and general steps for modifying the User Interface (UI) of 智字幕 (IntelliSubs), which is built using the `CustomTkinter` library.

Refer to [UI Design and Architecture](../architecture/ui_design.md) for an overview of the UI structure.

## Prerequisites

*   Basic understanding of Python.
*   Familiarity with GUI programming concepts (widgets, layouts, event handling).
*   Knowledge of Tkinter and specifically [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) is highly beneficial.
*   Development environment set up as per [Setup Development Environment](../setup_env.md).

## Key UI Files

*   **`intellisubs/ui/app.py`:** Contains `IntelliSubsApp`, the main application class and root window. Modifications here are usually for global app behavior, window properties, or top-level menu bars (if any).
*   **`intellisubs/ui/views/main_window.py`:** Contains `MainWindow`, the primary frame where most user interactions occur (file selection, controls, preview, export). This is where you'll likely make most UI layout and widget changes.
*   **`intellisubs/ui/widgets/`:** If custom, reusable widgets are created, they will reside here.

## Common UI Modification Tasks

### 1. Adding a New Widget (e.g., a Button, Label, Entry)

1.  **Identify Location:** Decide where the new widget should appear within `MainWindow` (or another relevant frame/view). Consider which existing frame it belongs to or if a new sub-frame is needed for layout.
2.  **Choose Widget Type:** Select the appropriate `CustomTkinter` widget (e.g., `ctk.CTkButton`, `ctk.CTkLabel`, `ctk.CTkEntry`, `ctk.CTkOptionMenu`, `ctk.CTkCheckBox`).
3.  **Instantiate and Configure:**
    *   In the `__init__` method of `MainWindow` (or the relevant class), instantiate the widget, passing `self` (or the parent frame) as the `master`.
    *   Configure its properties: `text`, `command` (for buttons), `variable` (for entry fields, option menus, checkboxes), `font`, `colors`, `width`, `height`, etc.
        ```python
        # In MainWindow.__init__
        self.new_button = ctk.CTkButton(self.controls_frame, text="New Action", command=self.on_new_action_click)
        ```
4.  **Layout (Packing/Gridding):**
    *   Use Tkinter's geometry managers (`.grid()`, `.pack()`, or rarely `.place()`) to position the widget within its parent frame. `MainWindow` primarily uses `.grid()`.
        ```python
        self.new_button.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        ```
    *   Ensure `grid_columnconfigure` and `grid_rowconfigure` are set appropriately on the parent frame if you want the widget or its column/row to expand when the window is resized.
5.  **Implement Event Handler (if interactive):**
    *   If the widget is interactive (like a button), create a new method in `MainWindow` to handle its event (e.g., `def on_new_action_click(self):`).
    *   This handler might:
        *   Read values from other widgets (e.g., `self.my_entry.get()`).
        *   Call methods on `self.app` or `self.app.workflow_manager`.
        *   Update other UI elements (e.g., `self.status_label.configure(text="...")`).

### 2. Modifying an Existing Widget

1.  **Locate the Widget:** Find the instantiation of the widget in `MainWindow.__init__` (or relevant file).
2.  **Change Properties:** Modify its configuration parameters (e.g., `text`, `state`, `values` for an option menu).
    ```python
    # Example: Change text and disable an existing button
    # self.existing_button.configure(text="Updated Text", state="disabled")
    ```
3.  **Adjust Layout:** If needed, change its `.grid()` or `.pack()` options.

### 3. Changing UI Layout

*   This involves modifying the `.grid()` or `.pack()` calls for multiple widgets.
*   You might need to add or remove `CTkFrame` instances to group widgets differently.
*   Adjust `rowspan`, `columnspan`, `sticky` options in `.grid()` to control how widgets fill their allocated space.
*   Remember to configure row/column weights (`grid_rowconfigure`, `grid_columnconfigure`) on parent frames if you want specific areas to expand more than others when the window resizes.

### 4. Handling User Input and Application State

*   **`ctk.StringVar`, `ctk.IntVar`, `ctk.BooleanVar`:** Use these Tkinter variable classes to link UI widgets (like `CTkEntry`, `CTkCheckBox`, `CTkOptionMenu`) to Python variables. Changes in the UI widget update the variable, and changes to the variable (via `var.set(...)`) update the UI.
*   **Accessing Configuration:** UI elements that reflect settings should get their initial values from `self.app.app_config` (loaded by `ConfigManager`). When a user changes a setting in the UI, update both the Tkinter variable and the corresponding key in `self.app.app_config`.
*   **Disabling/Enabling Widgets:** Change the `state` property of widgets (`state="normal"` or `state="disabled"`) to control user interaction based on application state (e.g., disable "Start" button during processing).

### 5. Running Long Tasks Without Freezing UI (Threading)

This is critical. Any task that takes more than a fraction of a second (like file processing, ASR, LLM calls) **must not** be run directly in an event handler (button command).

1.  **Create a Worker Function:** This function will perform the long task. It should not directly interact with UI widgets.
2.  **Use `threading` Module:**
    ```python
    import threading
    # In your event handler (e.g., button command method):
    def on_start_long_task(self):
        # Disable UI elements, show "processing" message
        self.start_button.configure(state="disabled")
        # ...

        # Create and start the worker thread
        thread = threading.Thread(target=self._perform_long_task_in_thread, args=(param1, param2))
        thread.daemon = True # Allows main app to exit even if thread is running (use with care)
        thread.start()

    def _perform_long_task_in_thread(self, arg1, arg2):
        try:
            # result = self.app.workflow_manager.some_long_process(arg1, arg2)
            result = "Placeholder result from thread" # Placeholder
            # Schedule UI update back on the main thread
            self.app.after(0, self._update_ui_after_thread, result, None)
        except Exception as e:
            # Schedule error handling on the main thread
            self.app.after(0, self._update_ui_after_thread, None, e)

    def _update_ui_after_thread(self, result, error):
        # This method is called by app.after(), so it runs in the main UI thread
        if error:
            # Update UI to show error (e.g., messagebox.showerror, update status label)
            print(f"Error from thread: {error}")
        else:
            # Update UI with result (e.g., populate textbox, enable buttons)
            print(f"Result from thread: {result}")
        
        # Re-enable UI elements
        self.start_button.configure(state="normal")
    ```
    *   `self.app.after(0, callback, *args)` is a Tkinter mechanism to schedule `callback` to run in the main UI event loop as soon as possible.

### 6. Styling and Theming

*   **CustomTkinter Themes:** Use `ctk.set_appearance_mode("Dark" / "Light" / "System")` and `ctk.set_default_color_theme("blue" / "green" / "dark-blue")` in `IntelliSubsApp` to change the overall look. These can be tied to settings in `ConfigManager`.
*   **Widget-Specific Colors:** Many CustomTkinter widgets accept `fg_color`, `text_color`, `border_color`, etc., parameters for fine-grained styling.
*   **Fonts:** Use `ctk.CTkFont(family="...", size=..., weight="...")` for custom fonts. Ensure the chosen fonts are commonly available or consider bundling them if licensing permits.

## Debugging UI Issues

*   **Print Statements:** Use `print()` liberally in event handlers and methods to trace execution flow and variable states.
*   **IDE Debugger:** Use your IDE's debugger (e.g., VS Code's Python debugger) to step through UI code.
*   **Isolate Components:** If a complex layout isn't working, try creating a minimal example with just those widgets in a separate test script to understand their behavior.
*   **Check Console for Tkinter Errors:** Tkinter/CustomTkinter errors often print stack traces to the console.

---

Modifying UI code requires careful attention to widget hierarchies, layout management, and event-driven programming. Always test your changes thoroughly.