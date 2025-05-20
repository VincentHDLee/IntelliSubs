# Troubleshooting Guide

This guide helps you diagnose and resolve common issues you might encounter while using or developing 智字幕 (IntelliSubs).

## General Troubleshooting Steps

1.  **Check Logs:** The first place to look for detailed error information is the application's log file.
    *   **Location:** Typically found in your user's application data directory (e.g., `%APPDATA%\IntelliSubs\logs\intellisubs.log` on Windows) or in a `logs` folder within the application's directory (for portable mode).
    *   The UI might have an option to "View Logs" or "Open Log Folder".
    *   Look for messages уровня `ERROR` or `CRITICAL`, and any stack traces.
2.  **Restart the Application:** Sometimes, a simple restart can resolve temporary glitches.
3.  **Check System Requirements:** Ensure your system meets the minimum requirements outlined in the [Installation Guide](./user_manual/installation.md#system-requirements).
4.  **Update Drivers:** If you're using GPU acceleration, ensure your NVIDIA graphics drivers are up to date.
5.  **Consult the FAQ:** Check the [User Manual FAQ](./user_manual/faq.md) for answers to common questions.

## Common Issues and Solutions

### 1. Application Fails to Start

*   **Symptom:** Double-clicking `IntelliSubs.exe` does nothing, or a brief error message flashes and disappears.
*   **Possible Causes & Solutions:**
    *   **Missing Dependencies:**
        *   Ensure all runtime dependencies are correctly installed/packaged. If running from source, make sure your virtual environment is activated and `pip install -r requirements.txt` was successful.
        *   **Microsoft Visual C++ Redistributable:** Some Python libraries (or their underlying C components) might need this. Try installing the latest version for your system architecture from Microsoft's website.
    *   **Corrupted Installation/Files:** Try reinstalling the application or re-extracting the portable version.
    *   **Log File Clues:** If a log file is created even partially, it might contain early startup errors.
    *   **Antivirus/Security Software:** Rarely, security software might interfere. Try temporarily disabling it (with caution) to see if it's the cause, or add an exception for IntelliSubs.
    *   **(Development) Path Issues:** If running from source, ensure your `PYTHONPATH` is set up correctly or you are running `python -m intellisubs.main` from the project root.

### 2. Error During File Processing

*   **Symptom:** An error message appears during subtitle generation (e.g., "Error during ASR transcription", "Error during audio preprocessing").
*   **Possible Causes & Solutions:**
    *   **Invalid/Corrupted Input File:**
        *   Try opening the audio/video file in another media player (like VLC) to ensure it's not corrupted.
        *   Ensure the file format is supported (see [Input and Output](./user_manual/features/input_output.md)).
    *   **FFmpeg Not Found/Working (for Audio Preprocessing):**
        *   If `ffmpeg-python` is used, it relies on an `ffmpeg` executable being available.
        *   Ensure `ffmpeg` is installed on your system and its `bin` directory is in your system's PATH environment variable.
        *   Alternatively, some packaged versions of IntelliSubs might bundle `ffmpeg`.
        *   Check logs for "ffmpeg" related errors.
    *   **ASR Model Issues:**
        *   **Model Not Downloaded:** If using a specific Whisper model for the first time, it might need to be downloaded. Ensure internet connectivity. Check log for download errors. Model files are usually cached in `~/.cache/huggingface/hub` or similar.
        *   **Corrupted Model File:** Rarely, a downloaded model file might be corrupt. Try deleting the cached model folder and letting the application re-download it.
        *   **Insufficient Resources for Model:** Larger models (medium, large) require significant RAM and VRAM (if using GPU). If your system is under-resourced, processing might fail or be extremely slow. Try a smaller model.
    *   **GPU Issues (if GPU mode is selected):**
        *   **CUDA/Driver Mismatch:** `faster-whisper` (and PyTorch, which it might use under the hood for CUDA operations) requires specific versions of CUDA Toolkit and NVIDIA drivers. Ensure your drivers are up-to-date. Check `faster-whisper` or PyTorch documentation for compatibility.
        *   **Insufficient GPU Memory (VRAM):** Larger ASR models consume more VRAM. If you run out, it will error. Try a smaller model or a compute type like `float16` or `int8` that uses less VRAM.
        *   The application should ideally fall back to CPU if GPU initialization fails.
    *   **LLM API Issues (if LLM Enhancement is enabled):**
        *   **Invalid API Key:** Double-check your LLM API key in the settings.
        *   **No Internet Connection:** Cloud LLMs require internet.
        *   **API Rate Limits:** You might have exceeded your usage quota or rate limits for the LLM service.
        *   **Incorrect API Endpoint/Model Name:** Verify LLM configuration.
    *   **File Permissions:** Ensure the application has read permission for the input file and write permission for the temporary directory and the final output directory.
    *   **Bugs in Code:** Check the application logs for Python stack traces that can pinpoint the issue.

### 3. Poor Transcription Quality

*   **Symptom:** Generated subtitles have many incorrect words, are poorly punctuated, or don't make sense.
*   **Possible Causes & Solutions:**
    *   **Poor Audio Quality:** Background noise, low volume, heavy accents, multiple overlapping speakers, or excessive reverb in the input audio will significantly degrade ASR accuracy. Try to use the clearest audio possible.
    *   **ASR Model Too Small:** For challenging audio, a `tiny` or `base` Whisper model might not be sufficient. Try a `small` or `medium` model in settings (this will increase processing time).
    *   **Incorrect Language Setting (Unlikely for v1.1):** Ensure the ASR is set to process Japanese.
    *   **Custom Dictionary Needed:** For specific jargon, names, or common mis-transcriptions relevant to your content, create and use a [Custom Dictionary](./user_manual/features/custom_dictionary.md).
    *   **Punctuation/Segmentation Issues:** The default rule-based punctuation and segmentation might not be perfect. LLM enhancement, if an option, can sometimes improve this.
    *   **LLM "Over-Correction":** Sometimes, an LLM might be too aggressive or misunderstand context, leading to unnatural phrasing. Try processing without LLM enhancement to compare.

### 4. UI is Frozen or Unresponsive

*   **Symptom:** The application window hangs, and you cannot click buttons or interact.
*   **Possible Cause:** A long-running task (like ASR processing) is being executed on the main UI thread instead of a background worker thread. This is a bug in the application.
*   **Solution (for Developers):** Ensure all time-consuming operations are offloaded to a separate `threading.Thread`, and communication back to the UI for updates is done in a thread-safe manner (e.g., using `app.after(0, callback)` or a queue).
*   **Solution (for Users):** You might have to forcefully close the application via Task Manager. Report this issue, noting what action you performed before it froze.

### 5. Output Subtitle File Issues

*   **Symptom:** Garbled text (`mojibake`) in the subtitle file when opened in a player or editor.
*   **Possible Cause:** Incorrect file encoding.
*   **Solution:**
    *   IntelliSubs defaults to **UTF-8** encoding, which is widely compatible.
    *   If your player/editor *requires* a different encoding (like Shift_JIS for some older Japanese software), check if IntelliSubs offers an encoding option during export or in settings.
    *   You can also try re-opening the subtitle file in a text editor (like Notepad++, VS Code) and re-saving it with the correct encoding.

## Reporting Issues

If you cannot resolve an issue using this guide:

1.  **Gather Information:**
    *   A clear description of the problem and the steps to reproduce it.
    *   The version of IntelliSubs you are using.
    *   Your Windows version.
    *   Any error messages displayed on screen.
    *   The relevant portion of the `intellisubs.log` file (please remove any personal sensitive data from the log before sharing, though IntelliSubs aims not to log such data).
    *   If possible, a small sample audio/video file that reproduces the issue (if the issue is file-specific and you can share the file).
2.  **Submit an Issue:** Report the problem on the project's [GitHub Issues page](https://github.com/VincentHDLee/IntelliSubs/issues).

---

This guide will be updated as more specific issues and solutions are identified.