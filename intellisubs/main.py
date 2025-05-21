# Main Entry Point for IntelliSubs Application
import sys
import os

# Ensure the 'intellisubs' package directory is in the Python path.
# This is crucial when running main.py directly (e.g., `python intellisubs/main.py`).
# If running as `python -m intellisubs.main`, it might be less critical but doesn't hurt.
current_dir = os.path.dirname(os.path.abspath(__file__))
# Assumes 'main.py' is inside 'intellisubs/' directory, and we want to add the parent of 'intellisubs/' to path.
project_root_dir = os.path.abspath(os.path.join(current_dir, ".."))

if project_root_dir not in sys.path:
    sys.path.insert(0, project_root_dir)
    # print(f"Added '{project_root_dir}' to sys.path for module import.")

try:
    from intellisubs.ui.app import IntelliSubsApp
    from intellisubs.utils.logger_setup import setup_logging
    # from intellisubs.utils.config_manager import ConfigManager # App usually handles its own config
except ImportError as e:
    # This block helps diagnose path issues if running script directly in a complex setup
    print("Error: Could not import IntelliSubs components.")
    print(f"Details: {e}")
    print("Ensure that the project root directory (containing the 'intellisubs' package) is in your PYTHONPATH,")
    print("or run the application as a module: `python -m intellisubs.main` from the project root.")
    sys.exit(1)


def main():
    """
    Main function to launch the IntelliSubs application.
    """
    # Initialize logging first
    # Config for logging could be loaded here or use defaults
    # For now, use default setup_logging.
    # A more advanced setup might load a basic config first to get log_level.
    logger = setup_logging() # Use default log level (INFO)
    logger.info("Application starting...")

    try:
        app = IntelliSubsApp()
        app.mainloop()
    except Exception as e:
        logger.critical("An unhandled exception occurred in the main application loop.", exc_info=True)
        print(f"Fatal Error: {e}") # Also print to console for visibility if logger fails or isn't visible
        # Potentially show an error dialog if GUI toolkit is still somewhat responsive
    finally:
        logger.info("Application shutdown.")

if __name__ == "__main__":
    # This allows the script to be run directly.
    # Add any pre-launch checks or setup here if needed.
    # For example, checking for essential dependencies or configurations.
    
    # Example: Force a specific theme for testing (CustomTkinter)
    # import customtkinter as ctk
    # ctk.set_appearance_mode("Light")
    
    main()