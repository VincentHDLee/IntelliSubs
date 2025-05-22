# Setting Up Development Environment

This guide outlines the steps to set up a local development environment for 智字幕 (IntelliSubs).

## Prerequisites

Before you begin, ensure you have the following installed on your system (Windows):

1.  **Python:**
    *   Version: Python 3.9+ (as specified in `DEVELOPMENT.md`). Python 3.10 or 3.11 are good choices.
    *   Download from [python.org](https://www.python.org/downloads/windows/).
    *   During installation, make sure to check the box **"Add Python X.Y to PATH"**.
2.  **Git:**
    *   Required for cloning the repository and version control.
    *   Download from [git-scm.com](https://git-scm.com/download/win).
3.  **C++ Build Tools (Potentially for some dependencies):**
    *   Some Python packages (especially those with C extensions) might require C++ build tools. If you encounter errors during `pip install` related to missing C++ compilers:
        *   Install "Build Tools for Visual Studio" from the [Visual Studio Downloads page](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio). Select the "C++ build tools" workload during installation.
4.  **(Optional but Recommended) A good Code Editor/IDE:**
    *   **Visual Studio Code (VS Code):** Highly recommended.
        *   Install the "Python" extension from Microsoft.
        *   Install the "Pylance" extension for better IntelliSense.
        *   (Optional) "Black Formatter" or "autopep8" extensions for code formatting.
    *   Other IDEs like PyCharm are also suitable.

## 1. Clone the Repository

First, clone the IntelliSubs repository to your local machine:

```bash
git clone https://github.com/VincentHDLee/IntelliSubs.git
cd IntelliSubs
```

If you plan to contribute, it's better to [fork the repository](https://docs.github.com/en/get-started/quickstart/fork-a-repo) first and then clone your fork:

```bash
git clone https://github.com/YOUR_USERNAME/IntelliSubs.git
cd IntelliSubs
# Optionally, add the original repository as an upstream remote
git remote add upstream https://github.com/VincentHDLee/IntelliSubs.git
```

## 2. Create and Activate a Virtual Environment

It is strongly recommended to use a virtual environment to manage project dependencies and avoid conflicts with system-wide Python packages.

Open your terminal (Command Prompt, PowerShell, or Git Bash) in the project's root directory (`IntelliSubs/`).

**Using `venv` (built-in):**

```bash
# Create a virtual environment named 'venv'
python -m venv venv

# Activate the virtual environment
# On Windows (Command Prompt/PowerShell):
venv\Scripts\activate
# On Windows (Git Bash):
source venv/Scripts/activate
# On macOS/Linux:
# source venv/bin/activate
```

You should see `(venv)` prefixed to your command prompt, indicating the virtual environment is active.

## 3. Install Dependencies

With the virtual environment activated, install the required Python packages listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

This command will download and install all necessary libraries, such as `faster-whisper`, `customtkinter`, `openai`, `pysrt`, etc.

If you encounter issues related to `ffmpeg-python` not finding `ffmpeg`, ensure `ffmpeg` is installed and accessible in your system's PATH, or consider installing it via a package manager like Chocolatey (`choco install ffmpeg`) or manually downloading it from [ffmpeg.org](https://ffmpeg.org/download.html) and adding its `bin` directory to your PATH.

### 3.1. Special Note for PyAudio Installation (Windows)

The `PyAudio` package, listed in `requirements.txt`, is essential for some audio processing capabilities (used by `pydub` for certain operations). However, its installation on Windows can sometimes fail if C++ Build Tools or PortAudio libraries are missing, leading to errors like `No module named 'pyaudioop'`.

If you encounter such an error after running `pip install -r requirements.txt`:

1.  **Ensure C++ Build Tools are installed:** As mentioned in the "Prerequisites" section ([`setup_env.md#L16`](docs/developer_guide/setup_env.md:16)), install "Build Tools for Visual Studio" with the "C++ build tools" workload. This is often a prerequisite for packages that need to compile C code during installation.

2.  **Install PyAudio using a precompiled wheel (Recommended for Windows):**
    This is often the most reliable method to avoid compilation issues on Windows.
    *   Go to the [Unofficial Windows Binaries for Python Extension Packages by Christoph Gohlke](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio).
    *   Download the `PyAudio` `.whl` file that matches:
        *   Your Python version (e.g., `cp39` for Python 3.9, `cp310` for Python 3.10, `cp311` for Python 3.11).
        *   Your system architecture (e.g., `win_amd64` for 64-bit Windows, `win32` for 32-bit Windows).
    *   Open your activated virtual environment terminal.
    *   Navigate to the directory where you downloaded the `.whl` file.
    *   Run the installation command, replacing the filename with the one you downloaded:
        ```bash
        pip install PyAudio‑0.2.14‑cp310‑cp310‑win_amd64.whl
        ```
        *(Example filename for PyAudio 0.2.14, Python 3.10, 64-bit Windows)*

3.  **Verify Installation**:
    After attempting the installation, you can verify it within your activated virtual environment by running Python and trying to import the modules:
    ```bash
    python
    ```
    Then, in the Python interpreter:
    ```python
    import pyaudio
    import pyaudioop
    exit()
    ```
    If no `ModuleNotFoundError` occurs, `PyAudio` and its components like `pyaudioop` should be correctly installed.

4.  **Alternative (If Gohlke's site is down or wheel not found):**
    You can try installing `pipwin` first, and then use `pipwin` to install `pyaudio`:
    ```bash
    pip install pipwin
    pipwin install pyaudio
    ```
    `pipwin` attempts to find and install unofficial precompiled binaries for you.

If you continue to face issues, please refer to the `docs/troubleshooting.md` guide or seek further assistance.

## 4. (Optional) IDE Setup - VS Code Example

If you are using VS Code:

1.  Open the `IntelliSubs` folder in VS Code (`File > Open Folder...`).
2.  VS Code should automatically detect the Python interpreter from your activated virtual environment (`venv`). If not, you can select it manually:
    *   Open the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`).
    *   Type `Python: Select Interpreter`.
    *   Choose the interpreter located in your `venv/Scripts/python.exe` (or `venv/bin/python`).
3.  Install recommended extensions if you haven't already (Python, Pylance).
4.  Configure a linter and formatter (see [Coding Standards](./coding_standards.md)).

## 5. Running the Application in Development Mode

To run the application from the source code:

1.  Ensure your virtual environment is activated.
2.  Navigate to the project root directory (`IntelliSubs/`) in your terminal.
3.  Run the main application script:

    ```bash
    python -m intellisubs.main
    ```
    Or, if you are in the `intellisubs` package directory itself:
    ```bash
    # cd intellisubs  (if you navigated into the package)
    # python main.py
    ```
    Using `python -m intellisubs.main` from the project root is generally more robust for package imports.

The IntelliSubs application window should now appear.

## 6. Running Tests

To run the unit tests (located in the `tests/` directory):

1.  Ensure your virtual environment is activated.
2.  Navigate to the project root directory (`IntelliSubs/`).
3.  Python's built-in `unittest` module can discover and run tests. A common way is:

    ```bash
    python -m unittest discover -s tests -p "test_*.py"
    ```
    Or, if you have `pytest` installed (you can add it to `requirements-dev.txt`):
    ```bash
    # pip install pytest  (if not already a project dev dependency)
    pytest
    ```
    `pytest` often provides more detailed output and has a richer ecosystem of plugins.

---

You are now set up to develop and contribute to IntelliSubs! Refer to other sections of the Developer Guide for information on coding standards, architecture, and more.