# Logger Setup Utility
import logging
import os
# from .file_handler import FileHandler # If needed for log directory creation

LOG_DIR_NAME = "logs"
LOG_FILE_NAME = "intellisubs.log"

def setup_logging(log_level=logging.INFO, log_to_console=True, log_to_file=True):
    """
    Configures the root logger for the application.

    Args:
        log_level: The minimum logging level to output (e.g., logging.DEBUG, logging.INFO).
        log_to_console (bool): Whether to output logs to the console.
        log_to_file (bool): Whether to output logs to a file.
    """
    logger = logging.getLogger("intellisubs") # Get a specific logger for the app
    if logger.hasHandlers(): # Avoid adding multiple handlers if called more than once
        logger.handlers.clear()

    logger.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s')

    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    if log_to_file:
        # Determine log directory (e.g., in user's app data or alongside executable for portable mode)
        # For simplicity, let's try to create it in the script's directory or user app data.
        
        log_dir_path = ""
        try:
            # Attempt to use user's app data directory
            app_data_dir = os.getenv('APPDATA') or os.getenv('LOCALAPPDATA')
            if app_data_dir:
                intellisubs_app_data_dir = os.path.join(app_data_dir, "IntelliSubs")
                if not os.path.exists(intellisubs_app_data_dir):
                    os.makedirs(intellisubs_app_data_dir, exist_ok=True)
                log_dir_path = os.path.join(intellisubs_app_data_dir, LOG_DIR_NAME)
            else: # Fallback to script's directory if APPDATA is not found
                # Fallback to the project root's 'logs' directory
                # Go up two levels from intellisubs/utils/logger_setup.py to project root
                project_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
                log_dir_path = os.path.join(project_root_dir, LOG_DIR_NAME)

            if not os.path.exists(log_dir_path):
                 os.makedirs(log_dir_path, exist_ok=True)
            
            log_file_path = os.path.join(log_dir_path, LOG_FILE_NAME)

            # Use a rotating file handler to prevent log files from growing indefinitely
            # from logging.handlers import RotatingFileHandler
            # file_handler = RotatingFileHandler(log_file_path, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
            
            # For simplicity now, a regular FileHandler
            file_handler = logging.FileHandler(log_file_path, encoding='utf-8', mode='a')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            logger.info(f"Logging to file: {log_file_path}")

        except Exception as e:
            logger.error(f"Failed to set up file logging to {log_dir_path}: {e}", exc_info=True)
            # Do not print, rely on console handler if enabled


    logger.info("IntelliSubs logger initialized.")
    return logger

if __name__ == '__main__':
    # Example usage:
    # Call this once at the beginning of your application
    # from intellisubs.utils.logger_setup import setup_logging # Assuming it's run from project root
    
    # If running this script directly for testing:
    # Adjust path for direct run if FileHandler is in the same directory
    # For this test, we assume a flat structure or that FileHandler is accessible.

    logger = setup_logging(log_level=logging.DEBUG)
    
    logger.debug("This is a debug message from logger_setup.")
    logger.info("This is an info message from logger_setup.")
    logger.warning("This is a warning message from logger_setup.")
    logger.error("This is an error message from logger_setup.")
    
    def test_function():
        logger.info("Logging from within a test function.")
        try:
            1 / 0
        except ZeroDivisionError:
            logger.error("A handled exception occurred in test_function.", exc_info=True) # exc_info=True adds stack trace

    test_function()
    print(f"Check for '{LOG_FILE_NAME}' in the logs directory (likely near this script or in APPDATA).")