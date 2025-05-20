# Installation Guide

This guide provides instructions on how to install and set up 智字幕 (IntelliSubs) on your Windows computer.

## System Requirements

*   **Operating System:** Windows 10 (64-bit) or Windows 11 (64-bit).
*   **Processor:** Modern multi-core CPU (Intel i5/AMD Ryzen 5 or better recommended for good performance, especially for CPU-based ASR).
*   **RAM:** 8 GB minimum, 16 GB recommended (especially if using larger ASR models or LLM features).
*   **Storage:**
    *   At least 500 MB for the application itself.
    *   Additional space for ASR models (can range from ~100MB for "tiny" models to over 2GB for "large" models). The default model will be bundled or downloaded on first run.
    *   Space for your audio/video files and generated subtitles.
*   **GPU (Optional but Recommended for Speed):**
    *   NVIDIA GPU with CUDA support (e.g., GTX 1060 6GB / RTX 2060 or newer) for significantly faster ASR processing. Ensure you have the latest NVIDIA drivers installed.
    *   (AMD GPU support via DirectML/ONNX Runtime might be considered for future versions if `faster-whisper` or other backends support it well).
*   **Internet Connection:**
    *   Required for downloading ASR models (if not bundled) or for using online LLM services.
    *   Not required for core offline ASR processing once models are downloaded.
*   **(Potentially) Microsoft Visual C++ Redistributable:** The application might require a specific version. If so, it will be bundled or a download link provided.

## Downloading IntelliSubs

You will be able to download IntelliSubs from the [GitHub Releases page](https://github.com/VincentHDLee/IntelliSubs/releases) (link will be active once releases are made).

Two types of packages will generally be available:

1.  **Installer (`IntelliSubs-vx.x.x-setup.exe`):** A standard Windows installer that will guide you through the setup process and create shortcuts.
2.  **Portable (`IntelliSubs-vx.x.x-portable.zip`):** A ZIP archive that you can extract anywhere and run directly without installation. Useful for running from a USB drive or avoiding system-wide installation.

## Running the Application

### Using the Installer

1.  Download the `IntelliSubs-vx.x.x-setup.exe` file.
2.  Double-click the downloaded `.exe` file to start the installation wizard.
3.  Follow the on-screen instructions. You may be able to choose an installation directory.
4.  Once installation is complete, you should find a shortcut for IntelliSubs on your Desktop and/or in your Start Menu.
5.  Double-click the shortcut to launch the application.

### Using the Portable Version

1.  Download the `IntelliSubs-vx.x.x-portable.zip` file.
2.  Extract the contents of the ZIP file to a folder of your choice (e.g., `C:\Program Files\IntelliSubsPortable` or `D:\Apps\IntelliSubs`).
3.  Navigate into the extracted folder.
4.  Find and double-click `IntelliSubs.exe` (or the main executable file) to launch the application.

## Initial Setup (If Applicable)

*   **Model Download:** On the first run, if the default ASR model is not bundled, the application might prompt you to download it or automatically start downloading it. Please ensure you have an internet connection for this step.
*   **Configuration:** Default settings should work for most users. You can access and change settings (like default ASR model, device, output paths) from within the application's settings/preferences menu (details will be in the `features` section of the manual).
*   **Firewall:** If you use online LLM services, your firewall might ask for permission for IntelliSubs to access the internet. Please allow it for these features to work.

---

If you encounter any issues during installation, please refer to the [Troubleshooting Guide](../troubleshooting.md).