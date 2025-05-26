# Main Application Class for IntelliSubs UI

import customtkinter as ctk
import os
from .views.main_window import MainWindow
from intellisubs.core.workflow_manager import WorkflowManager
from intellisubs.utils.config_manager import ConfigManager
from intellisubs.utils.logger_setup import setup_logging, mask_sensitive_data # Import the masking function

class IntelliSubsApp(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Logging is set up in main.py, but we can get the logger here if needed
        self.logger = setup_logging()
        self.logger.info("IntelliSubsApp: Initializing application.")

        self.title("智字幕 (IntelliSubs) v0.1.3 - 全球市场版")
        self.geometry("900x700") # Default size
        ctk.set_appearance_mode("System")  # Modes: "System" (default), "Dark", "Light"
        ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue"

        # Initialize configuration
        # Initialize configuration manager
        config_dir = os.path.join(os.path.expanduser("~"), ".intellisubs")
        if not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True) # Ensure directory exists
        self.config_path = os.path.join(config_dir, "config.json")
        self.config_manager = ConfigManager(self.config_path)
        self.app_config = self.config_manager.load_config()
        # Mask sensitive data before logging
        masked_app_config_for_log = mask_sensitive_data(self.app_config)
        self.logger.info(f"IntelliSubsApp: Config loaded from {self.config_path}: {masked_app_config_for_log}")


        # Initialize core workflow manager, passing the config and logger
        self.workflow_manager = WorkflowManager(config=self.app_config, logger=self.logger)
        self.logger.info("IntelliSubsApp: WorkflowManager initialized.")

        # Create and show the main window, passing necessary dependencies
        self.main_window = MainWindow(self, config=self.app_config, workflow_manager=self.workflow_manager, logger=self.logger, fg_color=self.cget("fg_color"))
        self.main_window.pack(side="top", fill="both", expand=True, padx=10, pady=10) # Added padx/pady for consistent look
        
        # Centralized status label in the app for global updates
        self.status_label = ctk.CTkLabel(self, text="状态: 就绪", font=ctk.CTkFont(size=12))
        self.status_label.pack(side="bottom", fill="x", pady=5)


        self.bind("<Control-q>", lambda event: self.quit_app())
        self.protocol("WM_DELETE_WINDOW", self.quit_app) # Handle window close button

        self.logger.info("IntelliSubsApp initialized.")

    def quit_app(self):
        self.logger.info("IntelliSubsApp: Quitting application...")
        # Save current config before quitting
        self.config_manager.save_config(self.app_config)
        self.logger.info("IntelliSubsApp: Configuration saved.")

        # Close resources held by WorkflowManager (like LLM HTTP client)
        if hasattr(self.workflow_manager, 'close_resources_sync'):
            self.logger.info("IntelliSubsApp: Closing WorkflowManager resources...")
            try:
                self.workflow_manager.close_resources_sync()
                self.logger.info("IntelliSubsApp: WorkflowManager resources closed.")
            except Exception as e:
                self.logger.error(f"IntelliSubsApp: Error closing WorkflowManager resources: {e}", exc_info=True)
        else:
            self.logger.warning("IntelliSubsApp: WorkflowManager does not have close_resources_sync method.")

        self.destroy()

if __name__ == "__main__":
    # This is for testing the App class directly.
    # The actual entry point will be in intellisubs/main.py
    app = IntelliSubsApp()
    app.mainloop()