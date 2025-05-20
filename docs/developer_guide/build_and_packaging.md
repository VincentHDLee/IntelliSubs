# Building and Packaging IntelliSubs

This guide covers how to build a distributable version of 智字幕 (IntelliSubs) for Windows, typically as a standalone `.exe` file or a folder containing the executable and its dependencies. We primarily use [PyInstaller](https://pyinstaller.org/) or [Nuitka](https://nuitka.net/) for this purpose, as outlined in `DEVELOPMENT.md`.

A helper script `scripts/build_app.py` (to be created) can automate some of these steps.

## Prerequisites

*   Development environment set up (see [Setup Development Environment](./setup_env.md)).
*   PyInstaller or Nuitka installed in your virtual environment:
    ```bash
    # In your activated venv
    pip install pyinstaller
    # OR
    # pip install nuitka orderedset zstandard # Nuitka has some specific deps
    ```
*   **(For Nuitka with MSVC on Windows)**: A C compiler is needed. Nuitka will usually try to find a compatible Visual Studio C++ compiler or MinGW64. Ensure "Build Tools for Visual Studio" (with C++ workload) is installed.
*   **(Optional) `upx`:** For further compressing the executable (can sometimes cause issues, use with caution). Download from [UPX GitHub](https://upx.github.io/) and add to PATH.

## General Packaging Considerations

*   **Assets and Resources:** Files in `intellisubs/ui/assets/` and `resources/` (like icons, default models, sample dictionaries) need to be bundled with the application.
    *   PyInstaller: Use the `--add-data` option in the `.spec` file or command line.
    *   Nuitka: Use `--include-data-dir` or `--include-data-file`.
*   **Hidden Imports:** Sometimes, PyInstaller or Nuitka might not automatically detect all necessary imports, especially for libraries that use dynamic imports or plugins (e.g., some `customtkinter` dependencies or specific `faster-whisper` model components if not handled by the library itself). These need to be specified as hidden imports.
    *   PyInstaller: `hiddenimports` in the `.spec` file or `--hidden-import` CLI option.
    *   Nuitka: `--include-module` or by ensuring the code explicitly imports them.
*   **Entry Point:** The main entry script for the application is `intellisubs/main.py`.
*   **One-File vs. One-Dir:**
    *   **One-File (`--onefile` for PyInstaller, default for Nuitka standalone):** Creates a single `.exe` file. Convenient for distribution, but startup can be slower as it extracts files to a temporary directory.
    *   **One-Dir (`--onedir` for PyInstaller, Nuitka default if not standalone):** Creates a folder containing the `.exe` and all its dependencies (DLLs, .pyd files, data files). Starts up faster, but requires distributing the entire folder. This is often better for debugging packaging issues.
*   **Console Window:** For GUI applications, you typically want to suppress the console window that appears when running the `.exe`.
    *   PyInstaller: Use the `-w` or `--noconsole` or `--windowed` option.
    *   Nuitka: Default for standalone GUI apps, or use `--windows-disable-console`.
*   **Application Icon:**
    *   PyInstaller: `-i path/to/app_icon.ico`
    *   Nuitka: `--windows-icon-from-ico=path/to/app_icon.ico`

## Method 1: Using PyInstaller

PyInstaller is generally easier to get started with for many Python applications.

1.  **Generate a `.spec` file (Recommended for customization):**
    *   Navigate to the project root in your activated virtual environment.
    *   Run PyInstaller once to generate a spec file:
        ```bash
        pyinstaller --name IntelliSubs --windowed --icon=resources/app_icon.ico intellisubs/main.py
        ```
        (Replace `resources/app_icon.ico` with the actual path to your icon if it's different or not yet created).
    *   This creates `IntelliSubs.spec` in the project root.

2.  **Edit the `.spec` file:**
    *   Open `IntelliSubs.spec` in a text editor. This file is Python code.
    *   **`datas`:** This is crucial for including assets and resources.
        ```python
        # Example for datas in .spec file
        a = Analysis(...)
        a.datas += [
            ('intellisubs/ui/assets', 'intellisubs/ui/assets'), # Source, Destination in bundle
            ('resources/default_models', 'resources/default_models'), # If bundling models
            ('resources/custom_dictionaries', 'resources/custom_dictionaries')
            # Add other resource directories or files here
        ]
        # For individual files: ('path/to/file.ico', '.')
        ```
        The second path in the tuple is the destination path *relative to the application's root in the bundle*.
    *   **`hiddenimports`:** Add any modules that PyInstaller fails to detect.
        ```python
        # a.hiddenimports = ['some_hidden_module', 'another_one']
        ```
        Common ones for CustomTkinter or plotting libraries might be needed. Check PyInstaller's warnings during build.
    *   **`pathex`:** Usually correctly set to your project root.
    *   Review other options like `bundle_files` in `COLLECT` for one-dir mode.

3.  **Build using the `.spec` file:**
    ```bash
    pyinstaller IntelliSubs.spec
    ```
    Or for a one-file executable (modify `onedir=True` to `onefile=True` in the `EXE` object within the spec file, or just use CLI options for simpler cases without a heavily modified spec):
    ```bash
    pyinstaller --name IntelliSubs --onefile --windowed --icon=resources/app_icon.ico \
                --add-data "intellisubs/ui/assets:intellisubs/ui/assets" \
                --add-data "resources:resources" \
                intellisubs/main.py
    ```
    *(Note: `--add-data` syntax for CLI varies slightly by OS for path separators, use `os.pathsep` or platform-specific separator in spec files).*

4.  **Output:**
    *   The bundled application will be in the `dist/IntelliSubs` folder (for one-dir) or as `dist/IntelliSubs.exe` (for one-file).
    *   The `build` folder contains intermediate files and can usually be deleted after a successful build.

## Method 2: Using Nuitka

Nuitka compiles Python code to C and then to an executable, which can sometimes offer better performance and obfuscation. It can be more complex to configure initially.

1.  **Basic Nuitka Command (One-File, Standalone):**
    *   Navigate to the project root in your activated virtual environment.
    *   ```bash
        python -m nuitka --mingw64  # (If using MinGW64, Nuitka might find MSVC automatically if installed)
                        --standalone 
                        --onefile 
                        --windows-disable-console
                        --windows-icon-from-ico=resources/app_icon.ico 
                        --include-package=customtkinter
                        --include-package=intellisubs # Important to include your own package
                        --include-data-dir=intellisubs/ui/assets=intellisubs/ui/assets 
                        --include-data-dir=resources=resources
                        # Add --include-module=some_module for hidden imports
                        --output-dir=dist_nuitka 
                        --output-filename=IntelliSubs.exe
                        intellisubs/main.py
        ```

2.  **Key Nuitka Options:**
    *   `--standalone`: Creates a self-contained folder (or a single file with `--onefile`).
    *   `--onefile`: Creates a single executable (implies `--standalone`).
    *   `--windows-disable-console`: Hides the console window for GUI apps.
    *   `--windows-icon-from-ico`: Sets the application icon.
    *   `--include-package=PACKAGENAME`: Forces inclusion of an entire package. Crucial for libraries like `customtkinter` and your own application package (`intellisubs`).
    *   `--include-module=MODULENAME`: Forces inclusion of a specific module (similar to hidden imports).
    *   `--include-data-files=SOURCE=DEST`: Includes a single data file.
    *   `--include-data-dir=SOURCE_DIR=DEST_DIR_IN_BUNDLE`: Includes an entire directory.
    *   `--output-dir`: Specifies the output directory.
    *   `--output-filename`: Specifies the name of the final executable.
    *   `--plugin-enable=tk-inter`: Nuitka has a plugin for Tkinter which it usually enables automatically if it detects Tkinter usage.
    *   `--plugin-enable=torch`: If `faster-whisper` uses PyTorch and Nuitka has issues, this might be relevant (though `faster-whisper` often uses CTranslate2 which might have its own Nuitka considerations).
    *   `--nofollow-imports` / `--follow-imports`: Control import following behavior.

3.  **Output:**
    *   The bundled application will be in the directory specified by `--output-dir` (e.g., `dist_nuitka/IntelliSubs.exe` along with supporting files if not `--onefile`).

## Helper Script (`scripts/build_app.py`) - Conceptual

A Python script can be created to automate these build commands, making it easier to produce consistent builds.

```python
# scripts/build_app.py (Highly simplified example)
import os
import shutil
import subprocess

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
APP_NAME = "IntelliSubs"
ENTRY_SCRIPT = os.path.join(PROJECT_ROOT, "intellisubs", "main.py")
ICON_PATH = os.path.join(PROJECT_ROOT, "resources", "app_icon.ico") # Ensure this exists
DIST_PATH = os.path.join(PROJECT_ROOT, "dist")

def build_with_pyinstaller():
    print("Building with PyInstaller...")
    spec_path = os.path.join(PROJECT_ROOT, f"{APP_NAME}.spec")

    # Clean previous builds
    if os.path.exists(DIST_PATH):
        shutil.rmtree(DIST_PATH)
    if os.path.exists(os.path.join(PROJECT_ROOT, "build", APP_NAME)):
        shutil.rmtree(os.path.join(PROJECT_ROOT, "build", APP_NAME))

    # Basic command - a .spec file is more robust for complex data/hidden imports
    cmd = [
        "pyinstaller",
        "--name", APP_NAME,
        "--noconfirm", # Overwrite output directory without asking
        "--windowed",
        # "--onefile", # Uncomment for one-file build
        f"--icon={ICON_PATH}",
        # Data files need careful handling with relative paths for spec or CLI
        # Example: --add-data "path_on_disk_from_root{os.pathsep}dest_in_bundle"
        f"--add-data={os.path.join(PROJECT_ROOT, 'intellisubs', 'ui', 'assets')}{os.pathsep}intellisubs/ui/assets",
        f"--add-data={os.path.join(PROJECT_ROOT, 'resources')}{os.pathsep}resources",
        # Add hidden imports if necessary: --hidden-import=some_module
        ENTRY_SCRIPT
    ]
    print(f"Executing: {' '.join(cmd)}")
    subprocess.run(cmd, check=True, cwd=PROJECT_ROOT)
    print(f"PyInstaller build complete. Output in {DIST_PATH}/{APP_NAME}")

if __name__ == "__main__":
    build_with_pyinstaller()
    # Add function for Nuitka if desired
```
*Note: The `os.pathsep` in `--add-data` is for PyInstaller's CLI syntax; it's usually `:` on Linux/macOS and `;` on Windows. In a `.spec` file, you use tuples `('source', 'destination')`.*

## Testing Packaged Application

After building, thoroughly test the packaged application on a clean Windows environment (or a virtual machine) that does not have your development setup. This helps catch missing dependencies or incorrect asset paths. Check:
* Startup.
* All UI interactions.
* Core functionality (processing a file).
* Log file creation.
* Config file creation and persistence.

Packaging can be an iterative process of identifying missing files or hidden imports and updating your build script or `.spec` file.