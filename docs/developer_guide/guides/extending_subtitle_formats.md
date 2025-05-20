# How-To: Extending Subtitle Formats

This guide explains how to add support for a new subtitle export format in 智字幕 (IntelliSubs).

The application uses an abstraction layer for subtitle formatting, defined by `intellisubs.core.subtitle_formats.base_formatter.BaseSubtitleFormatter`.

## Prerequisites

*   Understanding of the target subtitle format's syntax and specifications.
*   Familiarity with the `BaseSubtitleFormatter` interface in IntelliSubs.
*   Development environment set up as per [Setup Development Environment](../setup_env.md).

## Steps

1.  **Create a New Formatter Class:**
    *   In the `intellisubs/core/subtitle_formats/` directory, create a new Python file for your new format (e.g., `my_new_format_formatter.py`).
    *   Define a new class that inherits from `BaseSubtitleFormatter`:
        ```python
        # intellisubs/core/subtitle_formats/my_new_format_formatter.py
        from .base_formatter import BaseSubtitleFormatter
        # Import any helper libraries if needed (e.g., for timecode conversion, XML building)

        class MyNewFormatFormatter(BaseSubtitleFormatter):
            def __init__(self, **kwargs):
                """
                Initialize your new subtitle formatter.
                Store any format-specific configurations if needed.
                """
                print(f"MyNewFormatFormatter initialized.")
                # self.format_specific_option = kwargs.get("option_name", default_value)

            def format_subtitles(self, subtitle_entries: list) -> str:
                """
                Formats a list of subtitle entries into your new subtitle file format string.

                Args:
                    subtitle_entries (list): A list of dictionaries, where each dictionary
                                             represents a subtitle entry processed by SubtitleSegmenter.
                                             Example: {"text": "こんにちは\n世界", "start": 0.5, "end": 2.8}
                                             The 'text' field may contain newlines ('\n') for line breaks
                                             within a single subtitle cue. Your formatter needs to handle
                                             these newlines according to the target format's specification
                                             (e.g., SRT keeps them, ASS uses '\\N', VTT keeps them).

                Returns:
                    str: A string containing the formatted subtitle data for your new format.
                """
                formatted_content_parts = []

                # --- Header (if your format requires one) ---
                # formatted_content_parts.append("[Script Info Section or XML Header etc.]")
                # formatted_content_parts.append("Title: My New Format Subtitles")
                # formatted_content_parts.append("") # Blank line if needed

                # --- Styles (if your format supports them and you want a default) ---
                # formatted_content_parts.append("[V4+ Styles or CSS Styles Section]")
                # formatted_content_parts.append("Style: Default,Arial,20,&HFFFFFF,&H000000")
                # formatted_content_parts.append("")

                # --- Events/Cues Section ---
                # formatted_content_parts.append("[Events or Cue List]")
                # formatted_content_parts.append("Format: Start, End, TextContent, OtherParameters")


                for i, entry in enumerate(subtitle_entries):
                    if not all(k in entry for k in ["text", "start", "end"]):
                        print(f"Warning: Skipping invalid entry for MyNewFormat: {entry}")
                        continue

                    start_time = entry["start"] # seconds
                    end_time = entry["end"]   # seconds
                    text_content = entry["text"]  # May contain '\n'

                    # 1. Convert start_time and end_time to your format's specific timecode string.
                    #    Example for a hypothetical format HH:MM:SS.mmm
                    #    start_time_str = self.format_custom_timecode(start_time)
                    #    end_time_str = self.format_custom_timecode(end_time)
                    start_time_str = f"{start_time:.3f}" # Placeholder
                    end_time_str = f"{end_time:.3f}"   # Placeholder


                    # 2. Process text_content according to your format's newline and styling rules.
                    #    For example, if your format uses <br/> for newlines:
                    #    processed_text = text_content.replace('\n', '<br/>')
                    processed_text = text_content # Placeholder

                    # 3. Construct the subtitle entry string for your format.
                    #    Example: "CUE {i+1}\nSTART {start_time_str}\nEND {end_time_str}\n{processed_text}\n"
                    formatted_entry = f"ENTRY {i+1}\nTIME {start_time_str} --> {end_time_str}\nTEXT:\n{processed_text}\n---" # Placeholder
                    formatted_content_parts.append(formatted_entry)

                return "\n".join(formatted_content_parts)

            # Optional: Add helper methods for timecode formatting specific to your new format
            # def format_custom_timecode(self, seconds: float) -> str:
            #     # ... implementation ...
            #     return "HH:MM:SS.mmm" 
        ```

2.  **Update `WorkflowManager`:**
    *   The `WorkflowManager` (`intellisubs/core/workflow_manager.py`) needs to be able to use this new formatter.
    *   **`WorkflowManager.__init__`:**
        *   Import your new formatter class.
        *   Add an instance of your new formatter to the `self.formatters` dictionary, keyed by a short identifier for the format (e.g., "mnf" or "newformat").
            ```python
            # In WorkflowManager.__init__
            # from .subtitle_formats.my_new_format_formatter import MyNewFormatFormatter # Add import

            # ...
            # self.formatters = {
            #     "srt": SRTFormatter(),
            #     "lrc": LRCFormatter(),
            #     "ass": ASSFormatter(),
            #     "mynewformat": MyNewFormatFormatter() # Add your new formatter
            # }
            ```
    *   The `WorkflowManager.format_subtitle_data` method will then be able to use it if the `target_format` matches "mynewformat".

3.  **Update UI (Export Options):**
    *   Add your new format to the list of export options in the UI.
    *   In `intellisubs/ui/views/main_window.py`, modify the `self.export_options` list for the `CTkOptionMenu`:
        ```python
        # In MainWindow.__init__
        # self.export_options = ["SRT", "LRC", "ASS", "TXT", "MyNewFormat"] # Add your new format's display name
        # self.export_menu = ctk.CTkOptionMenu(..., values=self.export_options)
        ```
    *   Ensure the string value used in `export_options` (e.g., "MyNewFormat") maps to the key you used in `WorkflowManager.formatters` (e.g., "mynewformat" - usually by converting to lowercase in the `export_subtitles` method of `MainWindow`).
    *   Update the `file_types_map` in `MainWindow.export_subtitles` to include the file extension and description for your new format:
        ```python
        # In MainWindow.export_subtitles
        # file_types_map = {
        #     "srt": [("SubRip Subtitle", "*.srt")],
        #     ...,
        #     "mynewformat": [("My New Format File", "*.mnf")] # Add your format
        # }
        ```

4.  **Add Dependencies (If Any):**
    *   If your new formatter relies on external Python libraries (e.g., for complex XML building or specific format parsing/writing), add them to `requirements.txt`.

5.  **Documentation:**
    *   Update `DEVELOPMENT.md` if this new format is a core planned feature.
    *   Update the user manual (`docs/user_manual/features/subtitle_export.md`) to list and describe the new export format.
    *   Update this developer guide if there are specific nuances to your formatter.

6.  **Testing:**
    *   Create new unit tests for your `MyNewFormatFormatter` class in the `tests/core/subtitle_formats/` directory (e.g., `test_my_new_format_formatter.py`).
    *   Test with various `subtitle_entries` (empty, single line, multi-line text, different timings).
    *   Verify that the output string matches the specification of your new format.
    *   Perform integration tests to ensure it can be selected and used correctly via the `WorkflowManager` and the UI.

## Key Considerations for `format_subtitles` Implementation

*   **Input `subtitle_entries`:** Each `entry` in this list is a dictionary like `{"text": "Line1\nLine2", "start": 0.5, "end": 2.8}`.
    *   `text` is a string and may contain `\n` characters for intentional line breaks *within that subtitle cue*. Your formatter must handle these `\n` characters appropriately for the target format (e.g., SRT and VTT keep them, ASS converts to `\\N`, XML-based formats might use `<br/>`).
    *   `start` and `end` are float values representing seconds.
*   **Timecode Formatting:** Most subtitle formats have very specific timecode string requirements. Implement robust timecode conversion helper functions.
*   **Character Encoding:** The `BaseSubtitleFormatter.save_subtitles` method handles writing the file with a specified encoding (defaulting to UTF-8). Your `format_subtitles` method should just return the string content. Ensure your content is compatible with the intended encoding (UTF-8 is usually safest).
*   **Headers/Footers/Styles:** If your format requires specific headers, footers, or style definitions (like ASS or WebVTT with CSS), ensure these are correctly generated as part of the output string.

By following these steps, you can extend IntelliSubs to support a wide array of subtitle formats.