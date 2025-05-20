#!/bin/bash

# IntelliSubs Linting and Formatting Script
# This script is primarily for Unix-like environments (Linux, macOS, Git Bash on Windows).

# Ensure the script is run from the project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}" || exit 1

echo "Navigated to Project Root: $(pwd)"
echo "--- Running Black (Code Formatter) ---"

# Check if virtual environment exists and try to activate it
VENV_PATH="venv" # Common name for virtual environment folder
if [ -d "$VENV_PATH/bin/activate" ]; then # Unix-like venv
    echo "Activating virtual environment: $VENV_PATH (Unix-like)"
    source "$VENV_PATH/bin/activate"
elif [ -d "$VENV_PATH/Scripts/activate" ]; then # Windows Git Bash venv
    echo "Activating virtual environment: $VENV_PATH (Windows Git Bash)"
    source "$VENV_PATH/Scripts/activate"
else
    echo "Warning: Virtual environment '$VENV_PATH' not found or not activated."
    echo "Make sure Black and Flake8 are installed globally or in your active environment."
fi

# Run Black to format code
# The "." means format all files in the current directory and subdirectories
black .

# Check Black's exit code
if [ $? -ne 0 ]; then
    echo "Black formatting failed. Please review the changes or errors."
    # Deactivate venv if it was activated by the script
    if type deactivate &>/dev/null; then
        deactivate
    fi
    exit 1
fi
echo "Black formatting complete."

echo ""
echo "--- Running Flake8 (Linter) ---"

# Run Flake8 to check for style issues and errors
# The "." means lint all Python files in the current directory and subdirectories
flake8 .

# Check Flake8's exit code
if [ $? -ne 0 ]; then
    echo "Flake8 found issues. Please review and fix them."
    # Deactivate venv if it was activated by the script
    if type deactivate &>/dev/null; then
        deactivate
    fi
    exit 1
fi
echo "Flake8 found no issues."
echo ""
echo "Linting and formatting complete!"

# Deactivate virtual environment if it was activated by this script
if type deactivate &>/dev/null; then
    deactivate
    echo "Virtual environment deactivated."
fi

exit 0