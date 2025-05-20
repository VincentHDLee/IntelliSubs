# Feature: Previewing Subtitles

智字幕 (IntelliSubs) includes a preview area in its main interface that allows you to see the results of the subtitle generation process before exporting the final file. This is a crucial step for quickly assessing the quality of the transcription and formatting.

## The Preview Area

The preview area is typically a text box or a dedicated panel within the main application window.

**What it Displays:**

1.  **Processing Status:**
    *   While IntelliSubs is working on your audio/video file, the preview area will often display status messages, such as:
        *   "正在提取音频..." (Extracting audio...)
        *   "正在进行语音识别..." (Performing speech recognition...)
        *   "正在优化文本..." (Optimizing text...)
        *   Progress indicators (e.g., percentage complete, if available).

2.  **Generated Subtitle Text:**
    *   Once the ASR and text processing pipeline is complete, the generated subtitle text will be displayed in this area.
    *   The format of the preview might be:
        *   **Plain Text:** Just the transcribed words, perhaps with basic punctuation applied.
        *   **Formatted Preview (e.g., SRT-like):** It might show the text along with timestamps and segment numbers, similar to how it would appear in an SRT file. This helps you see the timing and line breaks.
        *   *(Refer to the `DEVELOPMENT.md` and application's current version for specifics on the preview format. Initial versions might show a simpler text preview, while later versions could offer more formatted views.)*

3.  **Error Messages:**
    *   If any errors occur during processing, detailed error messages or summaries will usually be shown in the preview area or a dedicated status bar/log window.

## Using the Preview

*   **Monitoring Progress:** Keep an eye on the preview area during processing to understand what stage the application is at.
*   **Initial Quality Check:** After processing is finished, carefully read through the previewed text. Check for:
    *   **Transcription Accuracy:** Are the Japanese words correctly transcribed?
    *   **Punctuation:** Is punctuation (「。」, 「、」, 「？」) generally correct and natural? (This depends on the effectiveness of the punctuation module or LLM enhancement).
    *   **Line Breaks:** If the preview shows line breaks (e.g., `\n`), do they occur at sensible places within sentences?
    *   **Speaker Names/Identifiers:** (If applicable and supported by a more advanced version) Are different speakers correctly identified?
    *   **Overall Readability:** Does the text flow well?
*   **No Direct Editing (Usually):** In most basic preview panes, you **cannot directly edit** the text within the preview box itself. The preview is for viewing only.
    *   If you need to make corrections, you would typically export the subtitle file (e.g., as SRT) and then edit it using a dedicated subtitle editing software (like Aegisub, Subtitle Edit, or even a plain text editor for SRT/LRC).
    *   *(Future versions of IntelliSubs might incorporate basic editing capabilities, but this is typically a more advanced feature.)*

## Why the Preview is Important

*   **Saves Time:** Quickly spot major errors without having to export and open the file in another program.
*   **Feedback Loop:** Helps you decide if you need to:
    *   Re-process with different ASR settings (e.g., a larger model for better accuracy).
    *   Adjust custom dictionary terms if specific words are consistently wrong.
    *   Enable/disable LLM enhancement based on its effect.
*   **Confidence Before Export:** Ensures you are reasonably satisfied with the quality before committing to an export.

---

Make it a habit to review the content in the preview area after each subtitle generation task. It's your first line of defense for quality control.