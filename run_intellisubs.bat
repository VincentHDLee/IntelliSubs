@echo off
echo Ensuring dependencies are installed...
pip install -r requirements.txt

echo.
echo Launching IntelliSubs...
python -m intellisubs.main

echo.
echo If the application failed to start, please ensure Python is correctly installed and in your PATH,
echo and that all dependencies in requirements.txt were installed successfully.
echo You can try running "pip install -r requirements.txt" manually in a command prompt.
pause