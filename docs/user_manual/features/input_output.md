# Feature: Input and Output Management

This section describes how to manage input audio/video files and configure output settings in 智字幕 (IntelliSubs).

## Supported Input File Types

IntelliSubs is designed to work with a variety of common audio and video formats. The primary focus is on extracting the Japanese audio track for ASR processing.

*   **Audio Files:**
    *   `MP3`
    *   `WAV` (Uncompressed PCM, various bit depths and sample rates supported via conversion)
    *   `M4A` (AAC audio)
    *   `OGG` (Vorbis audio - *support may depend on bundled ffmpeg capabilities*)
*   **Video Files (Audio will be extracted):**
    *   `MP4` (Commonly H.264/AAC)
    *   `MOV` (QuickTime format)
    *   `MKV` (Matroska container)
    *   Other common video formats supported by FFmpeg.

If you attempt to load an unsupported file type, the application should provide an error message.

## Selecting Input Files

### Single File Selection

1.  On the main application window, locate the **"选择文件" (Select File)** button.
2.  Click this button. A file dialog will open.
3.  Navigate to the directory containing your desired audio or video file.
4.  Select the file and click "Open".
5.  The full path to the selected file will be displayed in the input field next to the "选择文件" button.

### (Future Feature) Batch Processing / Folder Selection

*Currently, IntelliSubs primarily supports single file processing through the UI. Batch processing capabilities (e.g., selecting a folder and processing all supported files within it) may be added in future versions.*

## Configuring Default Input/Output Directories

By default, when you select a file, the "Save As" dialog for exporting subtitles will often open in the same directory as the input file or the last used directory.

The application also uses default `input` and `output` folders relative to the program's execution directory if no specific user configuration is found (especially relevant for initial setup or portable mode, as defined in `DEVELOPMENT.md`).

### User-Defined Persistent Paths (Through Settings)

IntelliSubs allows you to set persistent default input and output directories through its settings/preferences panel:

1.  Navigate to the application's **Settings** or **Preferences** menu/dialog.
2.  Look for sections مثل "Default Paths", "File Locations", or similar.
3.  You should find options to:
    *   **Set Default Input Folder:** When you click "选择文件", the file dialog will open to this folder by default.
    *   **Set Default Output Folder:** When you click "导出字幕", the "Save As" dialog will open to this folder by default, and generated files might be automatically saved here if a "quick export" option is used.
4.  Click "Browse" or a similar button next to each option to select your preferred default folder.
5.  Save your settings.

These settings are typically stored in the application's configuration file (e.g., `config.json` located in `%APPDATA%\IntelliSubs` or the application's portable directory).

## Auto-Open Output Directory (Optional Setting)

Some versions or configurations of IntelliSubs might offer a setting (e.g., "Automatically open output directory after export"). If enabled, the folder where your subtitle file was saved will automatically open in your system's file explorer after a successful export. This can be toggled in the application's settings.

---

Understanding these input/output mechanisms will help you streamline your workflow with IntelliSubs.