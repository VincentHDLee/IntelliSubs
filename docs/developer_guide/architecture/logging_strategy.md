# Logging Strategy

A robust logging strategy is essential for 智字幕 (IntelliSubs) to aid in debugging, monitoring application behavior, and allowing users to provide useful information when reporting issues. The `logger_setup.py` utility plays a key role in this.

*(Refer to `intellisubs/utils/logger_setup.py` for the implementation and `DEVELOPMENT.md` section 10 for the logging规范.)*

## Goals of Logging

*   **Debugging:** Provide detailed information for developers to trace issues and understand program flow during development and troubleshooting.
*   **Error Reporting:** Capture unhandled exceptions and critical errors with sufficient context (like stack traces) to help diagnose problems.
*   **Audit Trail (Basic):** Log key user actions and application lifecycle events for understanding how the application was used leading up to an issue.
*   **User Support:** Enable users to easily access and provide log files when they encounter problems, facilitating remote support.
*   **Performance Monitoring (Future):** Logs can be a source for identifying performance bottlenecks (e.g., by logging start/end times of critical operations).

## `logger_setup.py` Utility

*   **Role:** Provides a centralized function (`setup_logging`) to configure the root logger for the `intellisubs` application space.
*   **Key Features:**
    *   **Named Logger:** Uses `logging.getLogger("intellisubs")` to create/get a logger specific to the application, allowing for isolation from other libraries' logging.
    *   **Configurable Log Level:** The `setup_logging` function accepts a `log_level` argument (e.g., `logging.DEBUG`, `logging.INFO`, `logging.ERROR`). This level can be set based on a configuration value from `ConfigManager` or a command-line argument in the future.
    *   **Log Formatter:** Defines a standard log message format, including:
        *   Timestamp (`%(asctime)s`)
        *   Logger Name (`%(name)s` - which will be "intellisubs")
        *   Log Level (`%(levelname)s`)
        *   Module, Function Name, Line Number (`%(module)s.%(funcName)s:%(lineno)d`) for precise origin of the log message.
        *   The actual log message (`%(message)s`).
    *   **Console Handler (`StreamHandler`):**
        *   Optionally outputs log messages to the standard output/console (`sys.stdout`).
        *   Useful for real-time monitoring during development or when running from a terminal.
    *   **File Handler (`FileHandler` or `RotatingFileHandler`):**
        *   Optionally writes log messages to a file (e.g., `intellisubs.log`).
        *   **Log File Location:** The `logger_setup` utility attempts to place log files in a sensible user-accessible location:
            1.  Preferred: User's application data directory (e.g., `%APPDATA%\IntelliSubs\logs\intellisubs.log` on Windows).
            2.  Fallback: A `logs` subdirectory relative to the application's executable or script directory (useful for portable mode).
        *   **Rotation (Recommended):** While the initial placeholder might use a simple `FileHandler`, a `RotatingFileHandler` is recommended for production to prevent log files from growing indefinitely. It can be configured with `maxBytes` and `backupCount`.
        *   **Encoding:** Log files are written in UTF-8 to support all characters.
    *   **Avoid Duplicate Handlers:** Checks if the logger already has handlers before adding new ones, which is good practice if `setup_logging` could inadvertently be called multiple times.

## Integration and Usage

1.  **Initialization:**
    *   `setup_logging()` is called once, very early in the application startup sequence, typically in `intellisubs/main.py` *before* the main UI application (`IntelliSubsApp`) is instantiated.
    *   The desired initial log level can be passed to `setup_logging()`, potentially read from a command-line argument or a minimal, pre-UI config load if necessary. Otherwise, it uses a sensible default (e.g., `logging.INFO`).

2.  **Getting a Logger Instance in Modules:**
    *   Throughout the application (in core modules, UI modules, utils), individual modules should obtain a logger instance specific to their context (though often they will inherit from the "intellisubs" root logger settings):
        ```python
        import logging
        logger = logging.getLogger(__name__) # Best practice: use module's own name
        # Or, if you want to ensure it's part of the "intellisubs" hierarchy:
        # logger = logging.getLogger(f"intellisubs.{__name__}")

        def my_function():
            logger.info("This is an informational message from my_function.")
            try:
                # ... some operation ...
                if error_condition:
                    logger.error("An error occurred: specific details here.")
            except Exception as e:
                logger.exception("An unhandled exception was caught in my_function.")
                # logger.exception automatically includes stack trace info.
                # Equivalent to logger.error("...", exc_info=True)
        ```

## Log Levels (Guidance from `DEVELOPMENT.md`)

*   **`DEBUG`:** Detailed information, typically of interest only when diagnosing problems. Examples: variable values, specific steps in an algorithm, entry/exit of critical functions. Should be disabled in production by default but configurable.
*   **`INFO`:** Confirmation that things are working as expected. Examples: application start/shutdown, user initiating a major action (e.g., "User started subtitle generation for file X.mp4"), successful completion of a major task, configuration loaded.
*   **`WARNING`:** An indication that something unexpected happened, or an indication of some problem in the near future (e.g., ‘disk space low’). The software is still working as expected. Examples: optional module failed to load but core functionality is fine, a setting was found invalid and a default is being used, a non-critical API call failed but there's a fallback.
*   **`ERROR`:** Due to a more serious problem, the software has not been able to perform some function. Examples: file I/O error (cannot read input, cannot write output), ASR engine failed to initialize, critical API call failed with no fallback, unrecoverable error in a processing step.
*   **`CRITICAL`:** A serious error, indicating that the program itself may be unable to continue running. Example: unhandled exception in the main application loop. `logger.exception()` is often used here.

## Accessing Logs for Users

*   The UI should provide a simple way for users to access the log files, for example:
    *   A "View Logs" or "Open Log Folder" button/menu item in a "Help" or "About" section.
*   When users report issues, they should be encouraged to provide the `intellisubs.log` file.

## Security and Privacy

*   Avoid logging sensitive personal information (PII) unless absolutely necessary for debugging and with user awareness (e.g., file paths are common, but avoid logging API keys or file *content* unless in a specific debug mode).
*   API keys should **never** be logged.

This logging strategy ensures that IntelliSubs has a consistent and useful way of recording its operations, which is invaluable for development, support, and maintenance.