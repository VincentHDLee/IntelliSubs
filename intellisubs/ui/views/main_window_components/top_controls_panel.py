import customtkinter as ctk
from tkinter import filedialog
import os

class TopControlsPanel(ctk.CTkFrame):
    def __init__(self, master, app_ref, config, logger, start_processing_callback, main_window_ref, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app_ref # Reference to the main IntelliSubsApp instance
        self.main_window_ref = main_window_ref # Reference to the MainWindow instance for callbacks
        self.config = config
        self.logger = logger
        self.start_processing_callback = start_processing_callback

        self.grid_columnconfigure(1, weight=1) # Make file path entry expand

        self.file_label = ctk.CTkLabel(self, text="选择文件(可多选):")
        self.file_label.grid(row=0, column=0, padx=(10,0), pady=10, sticky="w")

        self.file_path_var = ctk.StringVar(value="未选择文件")
        self.file_entry = ctk.CTkEntry(self, textvariable=self.file_path_var, width=300, state="readonly")
        self.file_entry.grid(row=0, column=1, padx=5, pady=10, sticky="ew")

        self.browse_button = ctk.CTkButton(self, text="浏览...", command=self.browse_files, fg_color="#449D44", text_color_disabled="black")
        self.browse_button.grid(row=0, column=2, padx=(0,10), pady=10, sticky="e")
        
        self.start_button = ctk.CTkButton(self, text="开始生成字幕", command=self.start_processing_callback, state="disabled", fg_color="#EC971F", text_color_disabled="black")
        self.start_button.grid(row=1, column=0, columnspan=3, padx=10, pady=(5,5), sticky="ew")

        self.output_dir_label = ctk.CTkLabel(self, text="输出目录 (可选):")
        self.output_dir_label.grid(row=2, column=0, padx=(10,0), pady=(5,10), sticky="w")

        self.output_dir_var = ctk.StringVar(value=self.config.get("last_output_dir", ""))
        self.output_dir_entry = ctk.CTkEntry(self, textvariable=self.output_dir_var, width=250)
        self.output_dir_entry.grid(row=2, column=1, padx=5, pady=(5,10), sticky="ew")

        self.browse_output_dir_button = ctk.CTkButton(self, text="选择目录", command=self.browse_output_directory, fg_color="#449D44", text_color_disabled="black")
        self.browse_output_dir_button.grid(row=2, column=2, padx=(0,10), pady=(5,10), sticky="e")

        self.selected_file_paths = [] # Store list of selected file paths
        # self.output_directory = self.config.get("last_output_dir", None) # Handled by output_dir_var directly from config
        # if self.output_dir_var.get(): # Ensure var is also set if loaded from config
        #     self.output_dir_var.set(self.output_directory)


    def browse_output_directory(self):
        path = filedialog.askdirectory(title="选择输出目录")
        if path:
            # self.output_directory = path # No longer needed as separate var
            self.output_dir_var.set(path)
            self.config["last_output_dir"] = path # Save for next session
            self.app.config_manager.save_config(self.config)
            self.logger.info(f"输出目录选择: {path}")
            self.app.status_label.configure(text=f"状态: 输出目录已设置为 {os.path.basename(path)}")
            # Update export_all_button state in parent (MainWindow)
            # This will require a callback or direct access if MainWindow manages this button.
            # For now, MainWindow will be responsible for updating export_all_button state.
            # We can inform MainWindow that the output directory has changed.
            if hasattr(self.main_window_ref, 'update_export_all_button_state'):
                 self.main_window_ref.update_export_all_button_state()


    def browse_files(self):
        file_types = [
            ("Audio/Video Files", "*.mp3 *.wav *.m4a *.mp4 *.mov *.mkv *.ogg"),
            ("All files", "*.*")
        ]
        paths = filedialog.askopenfilenames(title="选择一个或多个音视频文件", filetypes=file_types)
        
        if paths:
            self.selected_file_paths = list(paths)
            self.file_path_var.set(f"已选择 {len(self.selected_file_paths)} 个文件")
            
            # Notify MainWindow to update file list display and other related UI
            if hasattr(self.main_window_ref, 'handle_file_selection_update'):
                self.main_window_ref.handle_file_selection_update(self.selected_file_paths)
            
            self.update_start_button_state_based_on_files() # Use the new method
            self.app.status_label.configure(text=f"状态: 已选择 {len(self.selected_file_paths)} 个文件")
            self.logger.info(f"文件选择: {len(self.selected_file_paths)} 个文件: {', '.join(self.selected_file_paths)}")
        else:
            if not self.selected_file_paths: # Only reset if no files were selected before cancelling
                self.file_path_var.set("未选择文件")
                if hasattr(self.main_window_ref, 'handle_file_selection_update'):
                    self.main_window_ref.handle_file_selection_update([]) # Pass empty list
                self.update_start_button_state_based_on_files() # Use the new method
    
    def get_selected_files(self):
        return self.selected_file_paths

    def get_output_directory(self):
        return self.output_dir_var.get().strip()

    def set_ui_for_processing(self, is_processing: bool):
        """Configures UI elements based on processing state."""
        if is_processing:
            self.start_button.configure(text="处理中...", state="disabled", fg_color="#EC971F", text_color_disabled="black") # Keep color during processing
            self.browse_button.configure(state="disabled", fg_color="#449D44", text_color_disabled="black") # Keep color
            self.browse_output_dir_button.configure(state="disabled", fg_color="#449D44", text_color_disabled="black") # Also disable this
        else:
            self.start_button.configure(text="开始生成字幕", fg_color="#EC971F") # text_color_disabled still applies if state becomes disabled
            # The actual state of start_button (normal/disabled) when not processing
            # should be determined by whether files are selected.
            # This is handled by update_start_button_state_based_on_files.
            self.browse_button.configure(state="normal", fg_color="#449D44")
            self.browse_output_dir_button.configure(state="normal", fg_color="#449D44") # Re-enable
            self.update_start_button_state_based_on_files() # Ensure correct state after processing

    def update_start_button_state_based_on_files(self):
        """Updates the start button state based on whether files are selected."""
        if self.selected_file_paths:
            self.start_button.configure(state="normal") # fg_color and text_color_disabled are sticky
        else:
            self.start_button.configure(state="disabled") # fg_color and text_color_disabled are sticky
            if hasattr(self.main_window_ref, 'app') and hasattr(self.main_window_ref.app, 'status_label'):
                self.main_window_ref.app.status_label.configure(text="状态: 请选择文件以开始生成字幕。")
    def update_file_path_display(self, num_files=None, message=None):
        if message:
            self.file_path_var.set(message)
        elif num_files is not None:
            if num_files > 0:
                self.file_path_var.set(f"已选择 {num_files} 个文件")
            else:
                self.file_path_var.set("未选择文件")

    # def set_start_button_state(self, state): # This method is now redundant
    #     self.start_button.configure(state=state)

    def set_output_directory_text(self, path: str):
        """Allows MainWindow to update the output directory entry text."""
        self.output_dir_var.set(path)