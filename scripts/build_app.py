# IntelliSubs Build Automation Script (Conceptual Example)
import os
import shutil
import subprocess
import platform

# --- Configuration ---
APP_NAME = "IntelliSubs"
ENTRY_SCRIPT_REL_PATH = os.path.join("intellisubs", "main.py") # Relative to project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")) # Assumes script is in 'scripts/'

ICON_REL_PATH = os.path.join("resources", "app_icon.ico") # Ensure this icon exists in resources/
# For .icns on macOS: os.path.join("resources", "app_icon.icns")

# Output directory for builds
DIST_PATH_ROOT = os.path.join(PROJECT_ROOT, "dist_builds")

# PyInstaller specific
PYINSTALLER_DIST_PATH = os.path.join(DIST_PATH_ROOT, "pyinstaller")
PYINSTALLER_BUILD_PATH = os.path.join(PROJECT_ROOT, "build") # PyInstaller's intermediate build dir
PYINSTALLER_SPEC_FILENAME = f"{APP_NAME}.spec"

# Nuitka specific (example paths)
NUITKA_DIST_PATH = os.path.join(DIST_PATH_ROOT, "nuitka")

# Data/Assets to include (source_in_project, destination_in_bundle)
# Paths are relative to PROJECT_ROOT for source, and relative to bundle root for destination.
ASSETS_TO_BUNDLE = [
    (os.path.join("intellisubs", "ui", "assets"), os.path.join("intellisubs", "ui", "assets")),
    (os.path.join("resources"), "resources"), # Bundles the entire resources folder
    # Example for a single file:
    # (os.path.join("resources", "some_other_file.txt"), "some_other_file.txt")
]

# Hidden imports (module names that PyInstaller/Nuitka might miss)
HIDDEN_IMPORTS = [
    "customtkinter",
    # Add other known problematic imports here, e.g.:
    # "engineio.async_drivers.threading" # Example if using something like python-socketio
]

# --- Helper Functions ---
def get_platform_specific_data_sep():
    """Returns the data separator for PyInstaller's --add-data based on OS."""
    return ';' if platform.system() == "Windows" else ':'

def clean_directory(dir_path):
    """Removes a directory if it exists."""
    if os.path.exists(dir_path):
        print(f"Cleaning directory: {dir_path}")
        shutil.rmtree(dir_path)

def run_command(cmd_list, cwd=PROJECT_ROOT):
    """Executes a command and prints its output."""
    print(f"Executing: {' '.join(cmd_list)}")
    try:
        process = subprocess.Popen(cmd_list, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8')
        for line in process.stdout:
            print(line, end='')
        process.wait()
        if process.returncode != 0:
            print(f"Error: Command failed with exit code {process.returncode}")
            return False
    except Exception as e:
        print(f"Error executing command: {e}")
        return False
    return True

# --- Build Functions ---

def build_with_pyinstaller(one_file=False, use_console=False):
    print(f"\n--- Starting PyInstaller Build ({'One-File' if one_file else 'One-Dir'}, Console: {use_console}) ---")
    
    clean_directory(os.path.join(PYINSTALLER_DIST_PATH, APP_NAME if not one_file else ""))
    if one_file:
         if os.path.exists(os.path.join(PYINSTALLER_DIST_PATH, f"{APP_NAME}.exe")):
            os.remove(os.path.join(PYINSTALLER_DIST_PATH, f"{APP_NAME}.exe"))
    clean_directory(PYINSTALLER_BUILD_PATH)
    if os.path.exists(os.path.join(PROJECT_ROOT, PYINSTALLER_SPEC_FILENAME)):
        os.remove(os.path.join(PROJECT_ROOT, PYINSTALLER_SPEC_FILENAME))

    os.makedirs(PYINSTALLER_DIST_PATH, exist_ok=True)

    cmd = [
        "pyinstaller",
        "--name", APP_NAME,
        "--noconfirm", # Overwrite output directory without asking
    ]

    if one_file:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir") # Default, but explicit

    if use_console:
        cmd.append("--console")
    else:
        cmd.append("--windowed") # or --noconsole

    icon_full_path = os.path.join(PROJECT_ROOT, ICON_REL_PATH)
    if os.path.exists(icon_full_path):
        cmd.extend(["--icon", icon_full_path])
    else:
        print(f"Warning: Icon file not found at {icon_full_path}")

    for src, dest in ASSETS_TO_BUNDLE:
        full_src_path = os.path.join(PROJECT_ROOT, src)
        if os.path.exists(full_src_path):
            cmd.extend(["--add-data", f"{full_src_path}{get_platform_specific_data_sep()}{dest}"])
        else:
            print(f"Warning: Asset source path not found: {full_src_path}")
            
    for hidden_import in HIDDEN_IMPORTS:
        cmd.extend(["--hidden-import", hidden_import])

    cmd.append(os.path.join(PROJECT_ROOT, ENTRY_SCRIPT_REL_PATH))
    
    # Specify distpath and workpath (buildpath)
    cmd.extend(["--distpath", PYINSTALLER_DIST_PATH])
    cmd.extend(["--workpath", PYINSTALLER_BUILD_PATH])


    if run_command(cmd):
        print(f"PyInstaller build successful. Output in: {os.path.join(PYINSTALLER_DIST_PATH, APP_NAME if not one_file else APP_NAME + '.exe')}")
    else:
        print("PyInstaller build failed.")

def build_with_nuitka(one_file=True, use_console=False):
    print(f"\n--- Starting Nuitka Build ({'One-File' if one_file else 'Standalone Dir'}, Console: {use_console}) ---")
    
    output_dir_nuitka = os.path.join(NUITKA_DIST_PATH, f"{APP_NAME}_nuitka_build")
    clean_directory(output_dir_nuitka) # Nuitka creates a .dist and .build inside output-dir for onefile
    os.makedirs(NUITKA_DIST_PATH, exist_ok=True)


    cmd = [
        "python", "-m", "nuitka",
        "--standalone", # Implied by onefile, but good to be explicit for clarity if onefile=False
    ]
    if one_file:
        cmd.append("--onefile")
    
    if platform.system() == "Windows":
        if use_console:
            cmd.append("--windows-console-mode=force") # Or keep default
        else:
            cmd.append("--windows-disable-console")
        
        icon_full_path = os.path.join(PROJECT_ROOT, ICON_REL_PATH)
        if os.path.exists(icon_full_path):
            cmd.extend(["--windows-icon-from-ico", icon_full_path])
        else:
            print(f"Warning: Icon file not found at {icon_full_path}")
    # Add macOS specific icon options if needed: --macos-app-icon
    
    cmd.extend(["--output-dir", NUITKA_DIST_PATH]) # Nuitka puts final exe/folder here
    cmd.extend(["--output-filename", f"{APP_NAME}.exe" if platform.system() == "Windows" else APP_NAME])


    for pkg in ["customtkinter", "intellisubs"]: # Crucial packages
        cmd.extend(["--include-package", pkg])
        
    for hidden_import in HIDDEN_IMPORTS:
         cmd.extend(["--include-module", hidden_import]) # Or --include-plugin- Obwohl das für Module ist

    for src, dest in ASSETS_TO_BUNDLE:
        full_src_path = os.path.join(PROJECT_ROOT, src)
        if os.path.exists(full_src_path):
            if os.path.isdir(full_src_path):
                cmd.extend(["--include-data-dir", f"{full_src_path}={dest}"])
            else: # It's a file
                cmd.extend(["--include-data-files", f"{full_src_path}={dest}"])
        else:
            print(f"Warning: Asset source path not found: {full_src_path}")

    # Plugins (Nuitka often auto-detects, but can be explicit)
    cmd.extend(["--plugin-enable=tk-inter"])
    # cmd.extend(["--plugin-enable=numpy"]) # If numpy is used extensively and causes issues
    # cmd.extend(["--plugin-enable=pytorch"]) # If faster-whisper or underlying torch has issues

    cmd.append(os.path.join(PROJECT_ROOT, ENTRY_SCRIPT_REL_PATH))

    if run_command(cmd):
        print(f"Nuitka build successful. Output in: {NUITKA_DIST_PATH}")
        # If onefile, the exe is directly in NUITKA_DIST_PATH.
        # If not onefile, a folder APP_NAME.dist is there.
    else:
        print("Nuitka build failed.")


if __name__ == "__main__":
    print("IntelliSubs Build Script")
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Platform: {platform.system()}")

    # --- Choose what to build ---
    
    # PyInstaller One-Directory (good for debugging packaging)
    build_with_pyinstaller(one_file=False, use_console=False)
    
    # PyInstaller One-File (for distribution)
    # build_with_pyinstaller(one_file=True, use_console=False)

    # Nuitka One-File (alternative for distribution)
    # build_with_nuitka(one_file=True, use_console=False)

    # Nuitka Standalone Directory
    # build_with_nuitka(one_file=False, use_console=False)

    print("\nBuild script finished.")