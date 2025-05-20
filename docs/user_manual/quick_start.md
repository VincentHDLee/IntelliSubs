# Quick Start Guide

This guide will walk you through the basic steps to generate your first subtitle file using 智字幕 (IntelliSubs).

## 1. Launch IntelliSubs

*   If you used the installer, find the IntelliSubs shortcut on your Desktop or Start Menu and double-click it.
*   If you are using the portable version, navigate to the folder where you extracted IntelliSubs and double-click `IntelliSubs.exe`.

## 2. Overview of the Main Interface

Upon launching, you will see the main window of IntelliSubs. It typically consists of:

*   **(A) File Selection Area:**
    *   An **input field** to show the path of the selected audio/video file.
    *   A **"选择文件" (Select File)** button to browse for your media file.
*   **(B) Control Buttons:**
    *   A **"开始生成字幕" (Start Generating Subtitles)** button to initiate the transcription and subtitle creation process.
*   **(C) Preview Area:**
    *   A **text box** where you can see the status of the processing and a preview of the generated subtitle text.
*   **(D) Export Area:**
    *   An **option menu** to select the desired subtitle format (e.g., SRT, LRC, ASS).
    *   An **"导出字幕" (Export Subtitles)** button to save the generated subtitles to a file.
*   **(E) Settings/Configuration Area (Optional):**
    *   This might be a separate panel or a menu option where you can configure ASR model size, processing device (CPU/GPU), LLM options, etc. (Refer to feature-specific documentation for details).
*   **(F) Status Bar (Optional):**
    *   Usually at the bottom, displaying messages about the current application state.

*(A visual screenshot of the main UI will be very helpful here in the actual documentation)*

## 3. Your First Subtitle Generation: Step-by-Step

Let's generate subtitles for a sample Japanese audio file.

### Step 1: Select Your Audio/Video File

1.  Click the **"选择文件" (Select File)** button (A).
2.  A file dialog will open. Navigate to the location of your Japanese audio (e.g., `.mp3`, `.wav`) or video (e.g., `.mp4`) file.
3.  Select the file and click "Open".
4.  The path to your selected file will appear in the input field (A). The "开始生成字幕" button (B) should now be enabled.

### Step 2: (Optional) Adjust Settings

*   For your first run, you can usually leave the default settings.
*   If you wish to change the ASR model size (e.g., from "small" to "medium" for potentially better accuracy but slower speed) or switch between CPU and GPU (if available), you would do so in the settings area (E).
    *   *Note: Larger models or GPU processing might require initial model downloads if not already present.*

### Step 3: Start Generating Subtitles

1.  Click the **"开始生成字幕" (Start Generating Subtitles)** button (B).
2.  The application will now start processing your file. This involves:
    *   Extracting audio (if it's a video file).
    *   Converting audio to a standard format.
    *   Running Automatic Speech Recognition (ASR).
    *   Performing text post-processing (punctuation, normalization).
    *   (Optional) LLM enhancement.
3.  You can monitor the progress in the Preview Area (C) or Status Bar (F). The "开始生成字幕" button will likely be disabled during processing.
    *   *Processing time will vary depending on the length of your audio, your computer's ASR model settings, and CPU/GPU performance.*

### Step 4: Preview the Generated Subtitles

1.  Once processing is complete, a success message will appear, and the generated subtitle text will be displayed in the Preview Area (C).
2.  Scroll through the text to get an initial idea of the transcription quality.

### Step 5: Export the Subtitles

1.  In the Export Area (D), select your desired subtitle format from the dropdown menu (e.g., "SRT").
2.  Click the **"导出字幕" (Export Subtitles)** button (D).
3.  A "Save As" dialog will appear. Choose a location and a name for your subtitle file (e.g., `my_video_subtitles.srt`).
4.  Click "Save".
5.  You should see a confirmation message that the file has been saved.

**Congratulations!** You have successfully generated your first subtitle file with IntelliSubs. You can now use this file with your video editing software or media player.

---

For more detailed information on each feature, please refer to the other sections of this User Manual. If you encounter any issues, check the [Troubleshooting Guide](../troubleshooting.md).