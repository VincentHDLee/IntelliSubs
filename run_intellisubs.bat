@echo off
SETLOCAL

REM Get the directory of the batch script (should be project root)
SET "SCRIPT_DIR=%~dp0"
REM Remove trailing backslash if present for consistency
IF "%SCRIPT_DIR:~-1%"=="\" SET "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

SET "VENV_DIR=%SCRIPT_DIR%\venv"
SET "VENV_PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
SET "VENV_PIP_EXE=%VENV_DIR%\Scripts\pip.exe"
SET "MAIN_MODULE_NAME=intellisubs.main"
SET "REQUIREMENTS_FILE=%SCRIPT_DIR%\requirements.txt"

ECHO Looking for virtual environment in: %VENV_DIR%

REM Check if venv activation script exists
IF NOT EXIST "%VENV_DIR%\Scripts\activate.bat" (
    ECHO.
    ECHO Virtual environment 'venv' not found in %VENV_DIR%.
    ECHO Attempting to create it automatically...
    ECHO Running: python -m venv "%VENV_DIR%"
    python -m venv "%VENV_DIR%"
    
    REM Check if venv creation was successful
    IF NOT EXIST "%VENV_DIR%\Scripts\activate.bat" (
        ECHO.
        ECHO ERROR: Failed to create virtual environment automatically in %VENV_DIR%.
        ECHO Please ensure Python is installed correctly and the command 'python -m venv venv'
        ECHO can be run successfully from your command prompt in the project root:
        ECHO   %SCRIPT_DIR%
        ECHO You may need to create the virtual environment manually as per README.md instructions.
        ECHO.
        GOTO END_SCRIPT
    )
    ECHO Virtual environment created successfully in %VENV_DIR%.
    ECHO NOTE: Dependencies will now be installed into this new environment.
    ECHO.
)

ECHO Virtual environment found. Activating...
CALL "%VENV_DIR%\Scripts\activate.bat"
ECHO Virtual environment activated.

ECHO.
ECHO Ensuring dependencies are installed/up-to-date using the virtual environment's pip...
IF EXIST "%VENV_PIP_EXE%" (
    "%VENV_PIP_EXE%" install -r "%REQUIREMENTS_FILE%"
) ELSE IF EXIST "%VENV_PYTHON_EXE%" (
    ECHO pip.exe not found directly in venv, trying 'python -m pip install ...'
    "%VENV_PYTHON_EXE%" -m pip install -r "%REQUIREMENTS_FILE%"
) ELSE (
    ECHO.
    ECHO WARNING: Could not find pip or python executable in the virtual environment.
    ECHO   Expected pip at: %VENV_PIP_EXE%
    ECHO   Expected python at: %VENV_PYTHON_EXE%
    ECHO Please ensure the virtual environment is correctly set up and dependencies are installed manually.
    ECHO This might happen if 'python -m venv venv' completed but the environment is corrupted.
    ECHO.
    REM Even if pip failed above, if PyAudio is the issue, try reinstalling it specifically if python exists
    IF EXIST "%VENV_PYTHON_EXE%" (
      GOTO ATTEMPT_PYAUDIO_REINSTALL
    )
    GOTO LAUNCH_APP_SECTION
)

REM :ATTEMPT_PYAUDIO_REINSTALL -- This section is no longer needed as PyAudio is removed from requirements.
REM ECHO.
REM ECHO Attempting to forcefully reinstall PyAudio to resolve potential issues...
REM IF EXIST "%VENV_PYTHON_EXE%" (
REM     "%VENV_PYTHON_EXE%" -m pip install --force-reinstall --no-cache-dir PyAudio
REM ) ELSE (
REM     ECHO Cannot attempt PyAudio reinstall as Python executable in venv is not found.
REM )

:LAUNCH_APP_SECTION
ECHO.
ECHO Launching IntelliSubs using Python from virtual environment as a module...
IF EXIST "%VENV_PYTHON_EXE%" (
    REM Ensure current directory is project root when running as a module
    PUSHD "%SCRIPT_DIR%"
    "%VENV_PYTHON_EXE%" -m %MAIN_MODULE_NAME%
    POPD
) ELSE (
    ECHO.
    ECHO ERROR: Python executable not found in virtual environment:
    ECHO   %VENV_PYTHON_EXE%
    ECHO Cannot start the application. This usually means venv creation or dependency installation failed.
    ECHO.
)

:END_SCRIPT
ECHO.
ECHO IntelliSubs script finished.
ENDLOCAL
pause