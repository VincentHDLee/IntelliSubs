# Feature: Subtitle Export

Once 智字幕 (IntelliSubs) has processed your audio/video file and generated the subtitle text, you can export it into various standard subtitle formats. This guide explains the available formats and export options.

## Supported Export Formats

IntelliSubs aims to support the following common subtitle formats, crucial for different video editing workflows and media players:

1.  **SRT (`.srt`) - SubRip Text**
    *   **Description:** One of the most widely supported and simplest text-based subtitle formats. It contains sequential numbered subtitle entries with start and end timestamps and the subtitle text.
    *   **Compatibility:** Supported by almost all video players (VLC, MPC-HC, Windows Media Player, etc.), video editing software (Adobe Premiere Pro, DaVinci Resolve, Final Cut Pro, Kdenlive, Shotcut), and online video platforms (YouTube, Vimeo).
    *   **Features:** Basic text formatting (bold, italic, underline via HTML-like tags) is sometimes supported by players, but IntelliSubs will primarily output plain text.
    *   **IntelliSubs Focus:** Core supported format, high priority.

2.  **LRC (`.lrc`) - LyRiCs**
    *   **Description:** A format commonly used for synchronized lyrics with music players, but can also be used for simple subtitles. Each line has a timestamp indicating when it should appear.
    *   **Compatibility:** Supported by many music players and some specialized video players or karaoke software. Less common for general video subtitles compared to SRT.
    *   **Features:** Primarily line-by-line synchronization. Does not typically support multi-line text per entry in the same way SRT does (usually one lyrical line per timestamp).
    *   **IntelliSubs Focus:** Supported format. Output will be structured to fit LRC conventions (e.g., one text line per timestamp).

3.  **ASS (`.ass`) - Advanced SubStation Alpha**
    *   **Description:** A powerful and flexible subtitle format that allows for advanced styling, positioning, and effects. Often used by fansubbing groups and for karaoke effects.
    *   **Compatibility:** Well-supported by players like VLC, MPC-HC (with VSFilter/xy-VSFilter), and Aegisub (a popular ASS subtitle editor). Professional video editors might require plugins or conversion to import ASS.
    *   **Features:** Supports rich text formatting, multiple styles, screen positioning, transparency, animations, karaoke effects (though IntelliSubs will initially support basic formatting).
    *   **IntelliSubs Focus:** Support for basic ASS structure and text output is planned. Advanced styling features will not be part of the initial offering but the format allows for later manual enhancement in tools like Aegisub.

4.  **TXT (`.txt`) - Plain Text (Optional)**
    *   **Description:** Outputs the raw, transcribed text without any timestamps or formatting.
    *   **Use Case:** Useful for quickly getting the ASR output as a simple script, for copy-pasting, or for feeding into other text processing tools.
    *   **IntelliSubs Focus:** May be offered as a simple export option for the raw ASR result before full subtitle formatting.

## How to Export Subtitles

1.  **Generate Subtitles:** First, process an audio/video file as described in the [Quick Start Guide](./quick_start.md). The generated text will appear in the preview area.
2.  **Select Export Format:**
    *   Locate the **Export Format** dropdown menu (usually near the "导出字幕" button).
    *   Click the dropdown and select your desired format (e.g., "SRT", "LRC", "ASS").
3.  **Click Export Button:**
    *   Click the **"导出字幕" (Export Subtitles)** button.
4.  **Save File Dialog:**
    *   A "Save As" dialog will appear.
    *   Navigate to the folder where you want to save your subtitle file.
    *   Enter a **File name**. The application will likely suggest a name based on your input file and the selected format (e.g., `my_video.srt`).
    *   The **"Save as type"** dropdown should already be pre-selected based on your format choice, but you can verify it.
    *   Click **"Save"**.
5.  A confirmation message should appear indicating the successful export.

## File Encoding Options

Subtitle files, especially those containing Japanese characters, need to be saved with the correct character encoding to avoid `mojibake` (garbled text).

*   **UTF-8 (Default and Recommended):**
    *   IntelliSubs will default to saving subtitle files in **UTF-8** encoding.
    *   UTF-8 is a universal encoding that supports Japanese and almost all other languages and is widely compatible with modern software and platforms.
*   **Shift_JIS (Optional):**
    *   For compatibility with some older Japanese software or specific workflows (e.g., if certain versions of video editors like an older剪映 (Jianying) have better Shift_JIS import for Japanese), IntelliSubs *may* offer an option in settings or during export to save in **Shift_JIS**.
    *   **Caution:** While Shift_JIS is specific to Japanese, UTF-8 is generally preferred for broader compatibility. Only use Shift_JIS if you have a specific reason.

The encoding option might be available in the application's **Settings** panel or potentially as an advanced option in the "Save As" dialog (though less common for simple UIs).

---

By providing these standard export formats, IntelliSubs aims to integrate smoothly into your existing content creation pipeline.