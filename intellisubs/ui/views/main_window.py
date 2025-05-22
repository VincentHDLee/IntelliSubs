# Main Window for IntelliSubs Application
import customtkinter as ctk
from tkinter import filedialog, messagebox # For dialogs
import os # Import the os module

class MainWindow(ctk.CTkFrame):
    def __init__(self, master, config, workflow_manager, logger, **kwargs):
        super().__init__(master, **kwargs)
        self.app = master # Reference to the main IntelliSubsApp instance
        self.config = config
        self.workflow_manager = workflow_manager
        self.logger = logger

        self.grid_columnconfigure(0, weight=1)
        # Adjust row configuration for new file list display and results
        self.grid_rowconfigure(1, weight=0) # For file_list_frame (fixed height or small weight)
        self.grid_rowconfigure(3, weight=1) # For results_frame (preview_textbox)

        # --- Top Controls Frame ---
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.controls_frame.grid_columnconfigure(1, weight=1) # Make file path entry expand

        self.file_label = ctk.CTkLabel(self.controls_frame, text="选择文件(可多选):") # Updated text
        self.file_label.grid(row=0, column=0, padx=(10,0), pady=10, sticky="w")

        self.file_path_var = ctk.StringVar(value="未选择文件") # Initial message
        self.file_entry = ctk.CTkEntry(self.controls_frame, textvariable=self.file_path_var, width=300, state="readonly") # Readonly for status
        self.file_entry.grid(row=0, column=1, padx=5, pady=10, sticky="ew")

        self.browse_button = ctk.CTkButton(self.controls_frame, text="浏览...", command=self.browse_files) # Renamed command
        self.browse_button.grid(row=0, column=2, padx=(0,10), pady=10, sticky="e")
        
        self.start_button = ctk.CTkButton(self.controls_frame, text="开始生成字幕", command=self.start_processing, state="disabled")
        self.start_button.grid(row=1, column=0, columnspan=3, padx=10, pady=(5,5), sticky="ew") # Adjusted pady

        # --- Output Directory Selection ---
        self.output_dir_label = ctk.CTkLabel(self.controls_frame, text="输出目录 (可选):")
        self.output_dir_label.grid(row=2, column=0, padx=(10,0), pady=(5,10), sticky="w")

        self.output_dir_var = ctk.StringVar(value=self.config.get("last_output_dir", "")) # Load last used or default
        self.output_dir_entry = ctk.CTkEntry(self.controls_frame, textvariable=self.output_dir_var, width=250) # Slightly less width than file_entry
        self.output_dir_entry.grid(row=2, column=1, padx=5, pady=(5,10), sticky="ew")

        self.browse_output_dir_button = ctk.CTkButton(self.controls_frame, text="选择目录", command=self.browse_output_directory)
        self.browse_output_dir_button.grid(row=2, column=2, padx=(0,10), pady=(5,10), sticky="e")

        # --- Selected Files List Frame ---
        self.file_list_frame = ctk.CTkFrame(self)
        self.file_list_frame.grid(row=1, column=0, padx=10, pady=(0,5), sticky="ew")
        self.file_list_frame.grid_columnconfigure(0, weight=1)
        self.file_list_frame.grid_rowconfigure(0, weight=1) # Allow textbox to expand if frame given weight

        self.selected_files_label = ctk.CTkLabel(self.file_list_frame, text="已选文件列表:")
        self.selected_files_label.grid(row=0, column=0, padx=(5,0), pady=(5,0), sticky="w")
        
        self.file_list_textbox = ctk.CTkTextbox(self.file_list_frame, wrap="none", height=100, state="disabled") # Height can be adjusted
        self.file_list_textbox.grid(row=1, column=0, padx=5, pady=5, sticky="ewns")
        # Add scrollbars if many files
        # self.file_list_scrollbar_y = ctk.CTkScrollbar(self.file_list_frame, command=self.file_list_textbox.yview)
        # self.file_list_scrollbar_y.grid(row=1, column=1, sticky="ns")
        # self.file_list_textbox.configure(yscrollcommand=self.file_list_scrollbar_y.set)
        # self.file_list_scrollbar_x = ctk.CTkScrollbar(self.file_list_frame, command=self.file_list_textbox.xview, orientation="horizontal")
        # self.file_list_scrollbar_x.grid(row=2, column=0, sticky="ew")
        # self.file_list_textbox.configure(xscrollcommand=self.file_list_scrollbar_x.set)


        # --- Settings Frame ---
        self.settings_frame = ctk.CTkFrame(self)
        self.settings_frame.grid(row=2, column=0, padx=10, pady=(5,10), sticky="ew") # Adjusted pady
        self.settings_frame.grid_columnconfigure((0,1,2,3), weight=1)

        self.asr_model_label = ctk.CTkLabel(self.settings_frame, text="ASR模型:")
        self.asr_model_label.grid(row=0, column=0, padx=(10,5), pady=5, sticky="w")
        self.asr_model_var = ctk.StringVar(value=self.config.get("asr_model", "small"))
        self.asr_model_options = ["tiny", "base", "small", "medium", "large"] # Add more as supported by faster-whisper
        self.asr_model_menu = ctk.CTkOptionMenu(self.settings_frame, variable=self.asr_model_var, values=self.asr_model_options, command=self.update_config)
        self.asr_model_menu.grid(row=0, column=1, padx=(0,10), pady=5, sticky="ew")

        self.device_label = ctk.CTkLabel(self.settings_frame, text="处理设备:")
        self.device_label.grid(row=0, column=2, padx=(10,5), pady=5, sticky="w")
        self.device_var = ctk.StringVar(value=self.config.get("device", "cpu"))
        self.device_options = ["cpu", "cuda", "mps"] # CUDA for Nvidia, MPS for Apple Silicon
        self.device_menu = ctk.CTkOptionMenu(self.settings_frame, variable=self.device_var, values=self.device_options, command=self.update_config)
        self.device_menu.grid(row=0, column=3, padx=(0,10), pady=5, sticky="ew")

        self.llm_checkbox_var = ctk.BooleanVar(value=self.config.get("llm_enabled", False))
        self.llm_checkbox = ctk.CTkCheckBox(self.settings_frame, text="启用LLM增强", variable=self.llm_checkbox_var, command=self.toggle_llm_options_and_update_config)
        self.llm_checkbox.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="w")

        # --- LLM Specific Settings (initially hidden/disabled if llm_checkbox is unchecked) ---
        self.llm_settings_frame = ctk.CTkFrame(self.settings_frame) # Nested frame for LLM settings
        self.llm_settings_frame.grid(row=2, column=0, columnspan=4, padx=5, pady=(0,5), sticky="ew")
        self.llm_settings_frame.grid_columnconfigure(1, weight=1) # Make entry fields expand

        self.llm_api_key_label = ctk.CTkLabel(self.llm_settings_frame, text="LLM API Key:")
        self.llm_api_key_label.grid(row=0, column=0, padx=(5,5), pady=5, sticky="w")
        self.llm_api_key_var = ctk.StringVar(value=self.config.get("llm_api_key", ""))
        self.llm_api_key_entry = ctk.CTkEntry(self.llm_settings_frame, textvariable=self.llm_api_key_var, show="*")
        self.llm_api_key_entry.grid(row=0, column=1, columnspan=3, padx=(0,5), pady=5, sticky="ew")

        self.llm_base_url_label = ctk.CTkLabel(self.llm_settings_frame, text="LLM Base URL (可选):")
        self.llm_base_url_label.grid(row=1, column=0, padx=(5,5), pady=5, sticky="w")
        self.llm_base_url_var = ctk.StringVar(value=self.config.get("llm_base_url", ""))
        self.llm_base_url_entry = ctk.CTkEntry(self.llm_settings_frame, textvariable=self.llm_base_url_var)
        self.llm_base_url_entry.grid(row=1, column=1, columnspan=3, padx=(0,5), pady=5, sticky="ew")
        
        self.llm_model_name_label = ctk.CTkLabel(self.llm_settings_frame, text="LLM 模型名称:")
        self.llm_model_name_label.grid(row=2, column=0, padx=(5,5), pady=5, sticky="w")
        self.llm_model_name_var = ctk.StringVar(value=self.config.get("llm_model_name", "gpt-3.5-turbo"))
        self.llm_model_name_entry = ctk.CTkEntry(self.llm_settings_frame, textvariable=self.llm_model_name_var)
        self.llm_model_name_entry.grid(row=2, column=1, columnspan=3, padx=(0,5), pady=5, sticky="ew")

        # --- Custom Dictionary Path Setting ---
        # This should be part of the main settings_frame, not llm_settings_frame
        # Let's add it after LLM checkbox and before the LLM specific frame, or as a new row in settings_frame.
        # For simplicity, adding as a new row in self.settings_frame (row 3, if LLM stuff is row 1 and 2)
        # Row 0: ASR Model, Device
        # Row 1: LLM Checkbox
        # Row 2: LLM Settings Frame (conditionally visible)
        # Row 3: Custom Dictionary

        self.custom_dict_label = ctk.CTkLabel(self.settings_frame, text="自定义词典 (CSV/TXT):")
        self.custom_dict_label.grid(row=3, column=0, padx=(10,5), pady=5, sticky="w")

        self.custom_dict_path_var = ctk.StringVar(value=self.config.get("custom_dictionary_path", ""))
        self.custom_dict_entry = ctk.CTkEntry(self.settings_frame, textvariable=self.custom_dict_path_var)
        self.custom_dict_entry.grid(row=3, column=1, columnspan=2, padx=(0,5), pady=5, sticky="ew")

        self.custom_dict_browse_button = ctk.CTkButton(self.settings_frame, text="浏览...", command=self.browse_custom_dictionary_file)
        self.custom_dict_browse_button.grid(row=3, column=3, padx=(0,10), pady=5, sticky="e")

        # --- Language Selection ---
        # New row for language selection in settings_frame (e.g., row 4)
        self.language_label = ctk.CTkLabel(self.settings_frame, text="处理语言:")
        self.language_label.grid(row=4, column=0, padx=(10,5), pady=5, sticky="w")

        self.language_var = ctk.StringVar(value=self.config.get("language", "ja"))
        # Language codes and their display names
        self.language_map = {"ja": "日本語 (Japanese)", "zh": "中文 (Chinese)", "en": "English"}
        self.language_display_options = list(self.language_map.values()) # Options for display
        self.language_codes = list(self.language_map.keys()) # Underlying codes

        # Find current display value based on config's language code
        current_display_language = self.language_map.get(self.language_var.get(), self.language_var.get())

        self.language_menu = ctk.CTkOptionMenu(
            self.settings_frame,
            variable=ctk.StringVar(value=current_display_language), # Use a separate var for display
            values=self.language_display_options,
            command=self.on_language_selected # New command handler
        )
        self.language_menu.grid(row=4, column=1, padx=(0,10), pady=5, sticky="ew")
        
        # --- Results Display & Preview Area ---
        self.results_outer_frame = ctk.CTkFrame(self)
        self.results_outer_frame.grid(row=3, column=0, padx=10, pady=(0,10), sticky="nsew")
        self.results_outer_frame.grid_columnconfigure(0, weight=1)
        # Row 0 for results list, Row 1 for preview text, Row 2 for export controls
        self.results_outer_frame.grid_rowconfigure(0, weight=2) # Give more weight to results list initially
        self.results_outer_frame.grid_rowconfigure(1, weight=1) # Preview text box

        self.results_label = ctk.CTkLabel(self.results_outer_frame, text="处理结果:", font=ctk.CTkFont(weight="bold"))
        self.results_label.grid(row=0, column=0, padx=5, pady=(5,0), sticky="w")

        self.result_list_scrollable_frame = ctk.CTkScrollableFrame(self.results_outer_frame, label_text="") # Removed label to use our own
        self.result_list_scrollable_frame.grid(row=0, column=0, padx=5, pady=(0,5), sticky="nsew")
        self.result_list_scrollable_frame.grid_columnconfigure(0, weight=1) # Allow items within to expand

        # Placeholder for dynamic result entries:
        # Example: You'll add CTkFrame instances here for each file result.
        # Each frame would contain: filename_label, status_label, preview_button.

        self.preview_label = ctk.CTkLabel(self.results_outer_frame, text="字幕预览:", font=ctk.CTkFont(weight="bold"))
        self.preview_label.grid(row=1, column=0, padx=5, pady=(5,0), sticky="w")
        
        self.preview_textbox = ctk.CTkTextbox(self.results_outer_frame, wrap="word", state="disabled", height=120) # Adjusted height
        self.preview_textbox.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        # Export controls frame, placed within results_outer_frame at the bottom
        self.export_controls_frame = ctk.CTkFrame(self.results_outer_frame)
        self.export_controls_frame.grid(row=2, column=0, padx=5, pady=(5,5), sticky="ew")
        self.export_controls_frame.grid_columnconfigure(2, weight=1) # Adjusted for new button

        self.export_format_var = ctk.StringVar(value="SRT")
        self.export_options = ["SRT", "LRC", "ASS", "TXT"]
        self.export_menu = ctk.CTkOptionMenu(self.export_controls_frame, variable=self.export_format_var, values=self.export_options)
        self.export_menu.grid(row=0, column=0, padx=(0,5), pady=5, sticky="w")
        
        self.export_button = ctk.CTkButton(self.export_controls_frame, text="导出当前预览", command=self.export_subtitles, state="disabled")
        self.export_button.grid(row=0, column=1, padx=5, pady=5, sticky="e")

        self.export_all_button = ctk.CTkButton(self.export_controls_frame, text="导出所有成功", command=self.export_all_successful_subtitles, state="disabled")
        self.export_all_button.grid(row=0, column=2, padx=(5,0), pady=5, sticky="e")
        
        # --- Old Settings Area (Placeholder, for reference) ---
        # self.settings_frame = ctk.CTkFrame(self, width=200) # Could be a right sidebar
        # self.settings_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="ns")
        # settings_label = ctk.CTkLabel(self.settings_frame, text="设置", font=ctk.CTkFont(size=16))
        # settings_label.pack(pady=10)
        # Add ASR model, device, LLM toggle, etc. here

        self.selected_file_paths = [] # Store list of selected file paths
        self.output_directory = self.config.get("last_output_dir", None) # Store selected output directory
        if self.output_directory: # Ensure var is also set if loaded from config
            self.output_dir_var.set(self.output_directory)

        self.generated_subtitle_data_map = {} # Dict to store {input_path: structured_subtitle_data}
        self.current_previewing_file = None # Path of the file whose subtitles are in preview_textbox

        self.toggle_llm_options_visibility() # Set initial visibility of LLM options

    def browse_output_directory(self):
        path = filedialog.askdirectory(title="选择输出目录")
        if path:
            self.output_directory = path
            self.output_dir_var.set(path)
            self.config["last_output_dir"] = path # Save for next session
            self.app.config_manager.save_config(self.config)
            self.logger.info(f"输出目录选择: {path}")
            self.app.status_label.configure(text=f"状态: 输出目录已设置为 {os.path.basename(path)}")
            # Update export_all_button state
            if self.generated_subtitle_data_map and any(self.generated_subtitle_data_map.values()): # Check if any successful results
                if path and os.path.isdir(path):
                    self.export_all_button.configure(state="normal")
                else:
                    self.export_all_button.configure(state="disabled")
            else:
                self.export_all_button.configure(state="disabled")


    def browse_files(self): # Renamed from browse_file
        file_types = [
            ("Audio/Video Files", "*.mp3 *.wav *.m4a *.mp4 *.mov *.mkv *.ogg"),
            ("All files", "*.*")
        ]
        # Use askopenfilenames to allow multiple selections
        paths = filedialog.askopenfilenames(title="选择一个或多个音视频文件", filetypes=file_types)
        
        if paths:
            self.selected_file_paths = list(paths) # Store as a list
            
            # Update the file_entry to show count
            self.file_path_var.set(f"已选择 {len(self.selected_file_paths)} 个文件")
            
            # Update the file_list_textbox
            self.file_list_textbox.configure(state="normal")
            self.file_list_textbox.delete("1.0", "end")
            for f_path in self.selected_file_paths:
                self.file_list_textbox.insert("end", os.path.basename(f_path) + "\n")
            self.file_list_textbox.configure(state="disabled")
            
            self.start_button.configure(state="normal")
            self.preview_textbox.configure(state="normal")
            self.preview_textbox.delete("1.0", "end")
            self.preview_textbox.insert("1.0", f"已选择 {len(self.selected_file_paths)} 个文件。\n点击“开始生成字幕”进行处理。")
            self.preview_textbox.configure(state="disabled")
            self.export_button.configure(state="disabled") # Disable export until a file is processed and previewed
            self.generated_subtitle_data_map = {} # Clear previous results
            self.current_previewing_file = None

            self.app.status_label.configure(text=f"状态: 已选择 {len(self.selected_file_paths)} 个文件")
            self.logger.info(f"文件选择: {len(self.selected_file_paths)} 个文件: {', '.join(self.selected_file_paths)}")
        else:
            # If user cancels dialog, and no files were previously selected, reset relevant UI
            if not self.selected_file_paths:
                self.file_path_var.set("未选择文件")
                self.file_list_textbox.configure(state="normal")
                self.file_list_textbox.delete("1.0", "end")
                self.file_list_textbox.configure(state="disabled")
                self.start_button.configure(state="disabled")


    def start_processing(self):
        if not self.selected_file_paths: # Check the list
            messagebox.showerror("错误", "请先选择一个或多个文件。")
            return

        self.start_button.configure(state="disabled")
        self.browse_button.configure(state="disabled")
        
        # Clear previous general preview, will update per file later
        self.preview_textbox.configure(state="normal")
        self.preview_textbox.delete("1.0", "end")
        self.preview_textbox.insert("1.0", f"开始处理 {len(self.selected_file_paths)} 个文件...\n")
        self.preview_textbox.configure(state="disabled")
        
        # Update status label in the main app window
        self.app.status_label.configure(text=f"状态: 正在处理 {len(self.selected_file_paths)} 个文件...")
        self.update_idletasks() # Ensure UI updates
        
        self.logger.info(f"开始批量处理 {len(self.selected_file_paths)} 个文件。")

        # Call the workflow manager in a separate thread to prevent UI freeze
        self.start_button.configure(text="处理中...", state="disabled") # This button state will be reset in _run_processing_in_thread
        self.export_button.configure(state="disabled")

        # Use a lambda to pass arguments to the threaded function
        import threading
        processing_thread = threading.Thread(target=self._run_processing_in_thread)
        processing_thread.start()
    
    def _run_processing_in_thread(self):
        try:
            # Clear previous results list
            self.app.after(0, self._clear_result_list)

            # Get current settings from UI, including output directory
            output_dir_to_use = self.output_dir_var.get().strip()
            if output_dir_to_use and not os.path.isdir(output_dir_to_use):
                self.logger.warning(f"指定的输出目录 '{output_dir_to_use}' 不存在或不是一个目录。将提示用户为每个文件选择保存位置。")
                # We could show a messagebox here, but it's in a thread. Better to handle in export.
                # For now, if invalid, export_subtitles will ask for path for each file.
                # If valid, export_subtitles should use it.
            
            # Persist output_dir_to_use if it's valid and different from stored
            if output_dir_to_use and os.path.isdir(output_dir_to_use) and self.config.get("last_output_dir") != output_dir_to_use:
                 self.config["last_output_dir"] = output_dir_to_use
                 # self.app.config_manager.save_config(self.config) # Config is saved at end of this method already

            asr_model = self.asr_model_var.get()
            device = self.device_var.get()
            llm_enabled = self.llm_checkbox_var.get()
            llm_api_key = self.llm_api_key_var.get().strip() # Strip whitespace
            # Aggressively clean base_url: remove all whitespace characters (space, tab, newline, etc.)
            raw_llm_base_url = self.llm_base_url_var.get()
            llm_base_url = "".join(raw_llm_base_url.split()) if raw_llm_base_url else ""
            llm_model_name = self.llm_model_name_var.get().strip() # Strip whitespace
            custom_dictionary_path = self.custom_dict_path_var.get().strip()
            processing_language = self.language_var.get() # Get selected language code

            # Update config manager with latest UI settings
            self.config["asr_model"] = asr_model
            self.config["device"] = device
            self.config["llm_enabled"] = llm_enabled
            self.config["llm_api_key"] = llm_api_key
            self.config["llm_base_url"] = llm_base_url if llm_base_url.strip() else None
            self.config["llm_model_name"] = llm_model_name
            self.config["custom_dictionary_path"] = custom_dictionary_path
            self.config["language"] = processing_language # Save selected language
            self.app.config_manager.save_config(self.config)

            # --- Batch Processing Logic ---
            processed_count = 0
            error_count = 0
            
            # Update overall status in main preview box (if desired, or use status_label)
            self.app.after(0, lambda: self.preview_textbox.configure(state="normal"))
            self.app.after(0, lambda: self.preview_textbox.delete("1.0", "end")) # Clear it for per-file status
            self.app.after(0, lambda: self.preview_textbox.insert("1.0", "开始批量处理...\n"))
            self.app.after(0, lambda: self.preview_textbox.configure(state="disabled"))

            for index, file_path in enumerate(self.selected_file_paths):
                base_filename = os.path.basename(file_path)
                self.logger.info(f"处理文件 ({index + 1}/{len(self.selected_file_paths)}): {file_path}, ASR模型: {asr_model}, 设备: {device}, LLM启用: {llm_enabled}")
                
                self.app.after(0, lambda fp=base_filename, i=index, total=len(self.selected_file_paths): self.app.status_label.configure(text=f"状态: 处理中 ({i+1}/{total}): {fp}"))
                self.app.after(0, lambda fp=base_filename: self._update_preview_for_status(f"正在处理: {fp}...\n"))


                try:
                    llm_params = None
                    if llm_enabled:
                        llm_params = {
                            "api_key": llm_api_key,
                            "base_url": self.config["llm_base_url"],
                            "model_name": llm_model_name
                        }

                    preview_text, structured_subtitle_data = self.workflow_manager.process_audio_to_subtitle(
                        audio_video_path=file_path,
                        asr_model=asr_model,
                        device=device,
                        llm_enabled=llm_enabled,
                        llm_params=llm_params,
                        output_format="srt",
                        current_custom_dict_path=custom_dictionary_path,
                        processing_language=processing_language # Pass selected language
                    )
                    
                    self.generated_subtitle_data_map[file_path] = structured_subtitle_data # Store by input path
                    
                    # Update UI for this file: Add to result list
                    self.app.after(0, lambda p=file_path, s_data=structured_subtitle_data, pt=preview_text, success=True, err_msg=None:
                                   self._add_result_entry(p, s_data, pt, success, err_msg))
                    
                    processed_count += 1
                    self.logger.info(f"文件 {file_path} 处理成功。")

                except Exception as e_file:
                    error_count += 1
                    self.logger.error(f"处理文件 {file_path} 时发生错误: {e_file}", exc_info=True)
                    # Update UI for this file: Add to result list with error
                    self.app.after(0, lambda p=file_path, success=False, err_msg=str(e_file):
                                   self._add_result_entry(p, None, None, success, err_msg))
            # --- End of Batch Processing ---
            final_status_msg = f"批量处理完成: {processed_count} 个成功, {error_count} 个失败。"
            self.logger.info(final_status_msg)
            self.app.after(0, lambda: self.app.status_label.configure(text=f"状态: {final_status_msg}"))
            
            if processed_count > 0:
                 # self.app.after(0, self.export_button.configure(state="normal")) # Export current preview button is enabled by _set_main_preview_content
                 if self.output_dir_var.get().strip() and os.path.isdir(self.output_dir_var.get().strip()):
                     self.app.after(0, self.export_all_button.configure(state="normal"))
                 else:
                     self.app.after(0, self.export_all_button.configure(state="disabled"))
                     
                 # If only one file was processed and successful, display its full preview.
                 # If multiple, the preview box already shows per-file status; user would click a file in a list to see its preview.
                 # For now, if multiple files, the preview_textbox retains the log-like status.
                 # We need a way to select a file from the (yet to be implemented) results list to show its preview.
                 if len(self.selected_file_paths) == 1 and self.selected_file_paths[0] in self.generated_subtitle_data_map:
                     first_file_path = self.selected_file_paths[0]
                     # Use export_subtitles from workflow_manager which returns the formatted string
                     preview_text_for_single = self.workflow_manager.export_subtitles(
                         self.generated_subtitle_data_map[first_file_path],
                         "srt"
                     )
                     self.app.after(0, lambda: self._set_main_preview_content(preview_text_for_single, first_file_path) )

            else: # No files processed successfully
                self.app.after(0, self.export_button.configure(state="disabled"))
                self.app.after(0, self.export_all_button.configure(state="disabled"))
                self.app.after(0, lambda: self._update_preview_for_status("所有文件处理失败或未生成字幕。\n"))


        except Exception as e_batch: # Catch errors in the overall setup/loop logic
            messagebox.showerror("批量处理错误", f"批量处理时发生意外错误: {e_batch}")
            self.app.after(0, lambda: self.app.status_label.configure(text="状态: 批量处理失败"))
            self.logger.exception(f"批量处理时发生意外错误: {e_batch}")
            self.app.after(0, lambda: self._update_preview_for_status(f"\n批量处理错误: {e_batch}\n"))
        finally:
            self.start_button.configure(text="开始生成字幕", state="normal")
            self.browse_button.configure(state="normal")
            # Ensure any UI updates are done in the main thread
            self.app.after(0, lambda: self.app.status_label.configure(text=self.app.status_label.cget("text"))) # Refresh status

    def _clear_result_list(self):
        """Clears all items from the result_list_scrollable_frame."""
        for widget in self.result_list_scrollable_frame.winfo_children():
            widget.destroy()
        # Also clear the main preview if needed, or handled by _add_result_entry logic
        self.preview_textbox.configure(state="normal")
        self.preview_textbox.delete("1.0", "end")
        self.preview_textbox.configure(state="disabled")
        self.current_previewing_file = None
        self.export_button.configure(state="disabled")
        self.export_all_button.configure(state="disabled")


    def _add_result_entry(self, file_path, structured_data, preview_text_for_this_file, success, error_message=None):
        """Adds an entry to the result_list_scrollable_frame."""
        base_name = os.path.basename(file_path)
        entry_frame = ctk.CTkFrame(self.result_list_scrollable_frame)
        entry_frame.pack(fill="x", pady=2, padx=2)

        status_text = "完成" if success else f"错误: {error_message[:50]}..." if error_message else "错误"
        status_color = "green" if success else "red"
        
        info_text = f"{base_name} - {status_text}"
        info_label = ctk.CTkLabel(entry_frame, text=info_text, text_color=status_color if not success else None)
        info_label.pack(side="left", padx=5, pady=2, expand=True, fill="x")

        if success and structured_data:
            preview_button = ctk.CTkButton(
                entry_frame,
                text="预览",
                width=60,
                command=lambda p=file_path, pt=preview_text_for_this_file: self._set_main_preview_content(pt, p)
            )
            preview_button.pack(side="right", padx=5, pady=2)

        # If this is the first item being added, and it's successful, auto-preview it.
        # Or if only one file was processed and it's this one.
        if success and (not self.current_previewing_file or len(self.selected_file_paths) == 1) :
            self._set_main_preview_content(preview_text_for_this_file, file_path)
            # self.export_button.configure(state="normal") # Handled by _set_main_preview_content

    # This _update_preview_for_status is now less relevant as _add_result_entry handles detailed status.
    # It was used for a monolithic preview box. We can remove or repurpose it if needed for global messages.
    # For now, let's comment it out to avoid confusion.
    # def _update_preview_for_status(self, message, data_for_main_preview=None, file_for_main_preview=None):
    #     """Helper to update the main preview textbox with status messages during batch, thread-safe via app.after."""
    #     self.preview_textbox.configure(state="normal")
    #     if data_for_main_preview and file_for_main_preview: # If specific content is provided for the main preview
    #         self.preview_textbox.delete("1.0", "end")
    #         self.preview_textbox.insert("1.0", data_for_main_preview)
    #         self.current_previewing_file = file_for_main_preview
    #     else: # Append status message
    #         self.preview_textbox.insert("end", message)
    #         self.preview_textbox.see("end") # Scroll to the end
    #         self.preview_textbox.configure(state="disabled")

    def _update_preview_for_status(self, message: str):
        """Appends a status message to the main preview textbox, thread-safe via app.after."""
        self.preview_textbox.configure(state="normal")
        self.preview_textbox.insert("end", message)
        self.preview_textbox.see("end") # Scroll to the end
        self.preview_textbox.configure(state="disabled")

    def _set_main_preview_content(self, content, file_path):
        """Sets the main preview textbox content, used for single file results or when a file is selected from a list."""
        self.preview_textbox.configure(state="normal")
        self.preview_textbox.delete("1.0", "end")
        if content:
            self.preview_textbox.insert("1.0", content)
        else:
            self.preview_textbox.insert("1.0", f"文件 {os.path.basename(file_path)} 未生成有效字幕预览。")
        self.preview_textbox.configure(state="disabled")
        self.current_previewing_file = file_path
        # Potentially enable export button if content is valid for this file
        if content and self.generated_subtitle_data_map.get(file_path):
             self.export_button.configure(state="normal")
        else:
             self.export_button.configure(state="disabled")


    def export_subtitles(self):
        # For multi-file, we need to know WHICH file's subtitles to export.
        # For now, this will export subtitles for self.current_previewing_file
        # This needs to be linked to the (future) results list selection.
        
        # Simplification: If only one file was processed successfully, export that.
        # If multiple, current_previewing_file should be set when user clicks on a (future) results list item.
        # For now, if multiple files were processed, but current_previewing_file is not set (e.g. user didn't click one yet),
        # or if no files were successfully processed, show a warning.

        target_file_to_export = None
        successful_files = [path for path, data in self.generated_subtitle_data_map.items() if data]

        if not successful_files:
            messagebox.showwarning("无数据", "没有成功处理的文件可供导出。")
            return

        if self.current_previewing_file and self.current_previewing_file in self.generated_subtitle_data_map:
            target_file_to_export = self.current_previewing_file
        elif len(successful_files) == 1:
            target_file_to_export = successful_files[0]
        else:
            # TODO: Prompt user to select which file to export from a list of successful files,
            # or this function should be disabled until a file is selected for preview from the results list.
            messagebox.showinfo("选择导出文件", "请先从（未来的）结果列表中选择一个已处理的文件以进行预览和导出。目前将尝试导出最近预览或唯一成功的文件。")
            # Fallback to the first successful one if current_previewing_file isn't set among them
            if successful_files: # Should always be true due to earlier check
                 target_file_to_export = successful_files[0]
                 # Prime the preview for this file if not already done
                 if self.current_previewing_file != target_file_to_export:
                     preview_text_for_export = self.workflow_manager.export_subtitles(
                         self.generated_subtitle_data_map[target_file_to_export],
                         "srt"
                     )
                     self._set_main_preview_content(preview_text_for_export, target_file_to_export)


        if not target_file_to_export or not self.generated_subtitle_data_map.get(target_file_to_export):
            messagebox.showwarning("无数据", "没有可导出的字幕数据，或当前选中的文件没有成功生成字幕。")
            return
            
        subtitle_data_to_export = self.generated_subtitle_data_map[target_file_to_export]
        export_format = self.export_format_var.get().lower()
        
        # Determine initial filename based on original file and selected format
        base_name_for_output = os.path.splitext(os.path.basename(target_file_to_export))[0]
        default_filename = f"{base_name_for_output}.{export_format}"
        
        file_types_map = {
            "srt": [("SubRip Subtitle", "*.srt"), ("All files", "*.*")],
            "lrc": [("LyRiCs Subtitle", "*.lrc"), ("All files", "*.*")],
            "ass": [("Advanced SubStation Alpha", "*.ass"), ("All files", "*.*")],
            "txt": [("Text File", "*.txt"), ("All files", "*.*")]
        }
        file_types = file_types_map.get(export_format, [("All files", "*.*")]) # Fallback

        # Use selected output directory if available and valid
        # self.output_directory is updated by browse_output_directory or loaded from config
        # self.output_dir_var.get() is what user might have typed
        
        chosen_output_dir = self.output_dir_var.get().strip()
        save_path = None

        if chosen_output_dir and os.path.isdir(chosen_output_dir):
            save_path = os.path.join(chosen_output_dir, default_filename)
            # Check for overwrite, or just save? For now, just save.
            # Optionally, could use asksaveasfilename with initialdir and initialfile if we want confirmation for each.
            # For simplicity, if output dir is set, we directly save.
            self.logger.info(f"使用选定输出目录: {chosen_output_dir}。 目标路径: {save_path}")
        else:
            if chosen_output_dir: # Path was specified but invalid
                 messagebox.showwarning("无效目录", f"指定的输出目录 '{chosen_output_dir}' 无效。请选择保存位置。")

            save_path = filedialog.asksaveasfilename(
                title=f"导出为 {export_format.upper()}",
                initialfile=default_filename,
                defaultextension=f".{export_format}",
                filetypes=file_types
            )

        if save_path:
            try:
                # Use the workflow manager to format the structured subtitle data into the desired export format
                self.logger.info(f"导出字幕为 {export_format.upper()} 格式到: {save_path}")
                final_data_to_save = self.workflow_manager.export_subtitles(
                    subtitle_data_to_export, # Corrected variable
                    export_format
                )

                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(final_data_to_save)
                messagebox.showinfo("成功", f"字幕已导出到: {os.path.basename(save_path)}")
                self.app.status_label.configure(text=f"状态: 已导出到 {os.path.basename(save_path)}")
                self.logger.info(f"字幕成功导出到: {save_path}")
            except Exception as e:
                messagebox.showerror("导出错误", f"导出字幕时发生错误: {e}")
                self.app.status_label.configure(text="状态: 导出失败")
                self.logger.exception(f"导出字幕时发生错误: {e}")

    def export_all_successful_subtitles(self):
        successful_items = {fp: data for fp, data in self.generated_subtitle_data_map.items() if data}
        if not successful_items:
            messagebox.showwarning("无数据", "没有成功处理的字幕可供导出。")
            return

        output_dir = self.output_dir_var.get().strip()
        if not output_dir or not os.path.isdir(output_dir):
            messagebox.showerror("错误", "请先在上方选择一个有效的输出目录。")
            # Optionally, trigger directory selection or just return
            # self.browse_output_directory()
            # if not self.output_dir_var.get().strip() or not os.path.isdir(self.output_dir_var.get().strip()):
            #    return # User cancelled or selected invalid directory
            return

        export_format = self.export_format_var.get().lower()
        exported_count = 0
        error_count = 0
        
        # Disable buttons during export all
        self.export_button.configure(state="disabled")
        self.export_all_button.configure(state="disabled")
        self.app.status_label.configure(text=f"状态: 正在批量导出 {len(successful_items)} 个文件...")
        self.update_idletasks() # Force UI update

        self.logger.info(f"开始批量导出所有成功字幕到目录: {output_dir}, 格式: {export_format.upper()}")

        for file_path, subtitle_data in successful_items.items():
            try:
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                output_filename = f"{base_name}.{export_format}"
                full_save_path = os.path.join(output_dir, output_filename)

                formatted_string = self.workflow_manager.export_subtitles(
                    subtitle_data,
                    export_format
                )
                with open(full_save_path, 'w', encoding='utf-8') as f:
                    f.write(formatted_string)
                self.logger.info(f"成功导出: {base_name} -> {output_filename}")
                exported_count += 1
            except Exception as e:
                self.logger.error(f"导出文件 {os.path.basename(file_path)} 时发生错误: {e}", exc_info=True)
                error_count += 1
        
        # Re-enable buttons
        # Re-enable export_button only if there's a current preview.
        if self.current_previewing_file and self.generated_subtitle_data_map.get(self.current_previewing_file):
            self.export_button.configure(state="normal")
        else:
            self.export_button.configure(state="disabled")

        # Re-enable export_all_button if still valid conditions
        if successful_items and output_dir and os.path.isdir(output_dir):
            self.export_all_button.configure(state="normal")
        else:
            self.export_all_button.configure(state="disabled")

        summary_message = f"批量导出完成: {exported_count} 个成功。"
        if error_count > 0:
            summary_message += f" {error_count} 个失败。"
        
        messagebox.showinfo("批量导出完成", summary_message)
        self.app.status_label.configure(text=f"状态: {summary_message}")
        self.logger.info(summary_message)

    def update_config(self, *args):
        """Updates the application configuration based on UI selections."""
        current_asr_model = self.asr_model_var.get()
        current_device = self.device_var.get()
        current_llm_enabled = self.llm_checkbox_var.get()
        current_llm_api_key = self.llm_api_key_var.get().strip() # Strip whitespace
        # Aggressively clean base_url: remove all whitespace characters
        raw_current_llm_base_url = self.llm_base_url_var.get()
        current_llm_base_url = "".join(raw_current_llm_base_url.split()) if raw_current_llm_base_url else ""
        current_llm_model_name = self.llm_model_name_var.get().strip()
        current_custom_dict_path = self.custom_dict_path_var.get().strip()
        current_selected_language = self.language_var.get() # Get language code from self.language_var

        changed = False
        if self.config.get("asr_model") != current_asr_model:
            self.config["asr_model"] = current_asr_model
            self.logger.info(f"配置更新: ASR模型设置为 '{current_asr_model}'")
            changed = True
        
        if self.config.get("device") != current_device:
            self.config["device"] = current_device
            self.logger.info(f"配置更新: 处理设备设置为 '{current_device}'")
            changed = True

        if self.config.get("llm_enabled") != current_llm_enabled:
            self.config["llm_enabled"] = current_llm_enabled
            self.logger.info(f"配置更新: LLM增强设置为 '{'启用' if current_llm_enabled else '禁用'}'")
            changed = True
        
        if self.config.get("llm_api_key") != current_llm_api_key:
            self.config["llm_api_key"] = current_llm_api_key
            self.logger.info(f"配置更新: LLM API Key已更改。") # Avoid logging the key itself
            changed = True

        processed_base_url = current_llm_base_url.strip() if current_llm_base_url else None
        if self.config.get("llm_base_url") != processed_base_url:
            self.config["llm_base_url"] = processed_base_url
            self.logger.info(f"配置更新: LLM Base URL设置为 '{processed_base_url if processed_base_url else '无'}'")
            changed = True

        if self.config.get("llm_model_name") != current_llm_model_name:
            self.config["llm_model_name"] = current_llm_model_name
            self.logger.info(f"配置更新: LLM 模型名称设置为 '{current_llm_model_name}'")
            changed = True

        if self.config.get("custom_dictionary_path") != current_custom_dict_path:
            self.config["custom_dictionary_path"] = current_custom_dict_path
            self.logger.info(f"配置更新: 自定义词典路径设置为 '{current_custom_dict_path if current_custom_dict_path else '无'}'")
            changed = True
        
        if self.config.get("language") != current_selected_language:
            self.config["language"] = current_selected_language
            self.logger.info(f"配置更新: 处理语言设置为 '{current_selected_language}'")
            changed = True

        if changed:
            self.app.config_manager.save_config(self.config)
            self.app.status_label.configure(text="状态: 配置已更新。")
        # else: # No need to say "not changed" if only language was selected from menu
            # self.app.status_label.configure(text="状态: 配置未更改。")

    def on_language_selected(self, selected_display_name: str):
        """Handles language selection from the OptionMenu."""
        # Find the language code corresponding to the display name
        selected_lang_code = "ja" # Default if not found
        for code, display_name in self.language_map.items():
            if display_name == selected_display_name:
                selected_lang_code = code
                break
        
        self.language_var.set(selected_lang_code) # Update the actual variable holding the code
        
        if self.config.get("language") != selected_lang_code:
            self.config["language"] = selected_lang_code
            self.app.config_manager.save_config(self.config)
            self.logger.info(f"处理语言已更改为: {selected_lang_code} ({selected_display_name})")
            self.app.status_label.configure(text=f"状态: 语言已更改为 {selected_display_name}。")
        # No need to call full update_config here, as it might be heavy.
        # The language_var is updated, and config is saved.
        # _run_processing_in_thread will pick up self.language_var.get()

    def browse_custom_dictionary_file(self):
        """Opens a file dialog to select a custom dictionary file."""
        file_types = [
            ("CSV files", "*.csv"),
            ("Text files", "*.txt"),
            ("All files", "*.*")
        ]
        selected_path = filedialog.askopenfilename(
            title="选择自定义词典文件",
            filetypes=file_types,
            initialdir=os.path.dirname(self.custom_dict_path_var.get()) if self.custom_dict_path_var.get() else os.getcwd()
        )
        if selected_path:
            self.custom_dict_path_var.set(selected_path)
            self.config["custom_dictionary_path"] = selected_path
            self.app.config_manager.save_config(self.config)
            self.logger.info(f"自定义词典路径已更新为: {selected_path}")
            self.app.status_label.configure(text=f"状态: 自定义词典路径已更新。")


    def toggle_llm_options_visibility(self):
        """Toggles the visibility of LLM specific settings based on the checkbox."""
        if self.llm_checkbox_var.get():
            self.llm_api_key_label.configure(state="normal")
            self.llm_api_key_entry.configure(state="normal")
            self.llm_base_url_label.configure(state="normal")
            self.llm_base_url_entry.configure(state="normal")
            self.llm_model_name_label.configure(state="normal")
            self.llm_model_name_entry.configure(state="normal")
            # Make the frame visible by managing its grid status
            self.llm_settings_frame.grid()
        else:
            self.llm_api_key_label.configure(state="disabled")
            self.llm_api_key_entry.configure(state="disabled")
            self.llm_base_url_label.configure(state="disabled")
            self.llm_base_url_entry.configure(state="disabled")
            self.llm_model_name_label.configure(state="disabled")
            self.llm_model_name_entry.configure(state="disabled")
            # Hide the frame
            self.llm_settings_frame.grid_remove()

    def toggle_llm_options_and_update_config(self, *args):
        """Called when the LLM checkbox state changes."""
        self.toggle_llm_options_visibility()
        self.update_config() # Then update and save the config

if __name__ == '__main__':
    # For testing MainWindow independently
    # This requires IntelliSubsApp to be defined or a mock master
    class MockApp(ctk.CTk):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.title("MainWindow Test")
            self.geometry("900x700")
            # Mock essential attributes that MainWindow expects from its master (app)
            self.config_manager = ConfigManager("mock_config.json") # A dummy config for testing
            self.app_config = self.config_manager.load_config()
            self.logger = setup_logging(log_file="mock_app.log")
            self.workflow_manager = WorkflowManager(config=self.app_config, logger=self.logger) # Mock workflow manager
            self.status_label = ctk.CTkLabel(self, text="Mock Status: 就绪")
            self.status_label.pack(side="bottom", fill="x")

    app_test = MockApp()
    main_frame = MainWindow(master=app_test, config=app_test.app_config,
                            workflow_manager=app_test.workflow_manager, logger=app_test.logger)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)
    app_test.mainloop()

    # Clean up mock config file
    if os.path.exists("mock_config.json"):
        os.remove("mock_config.json")
    if os.path.exists("mock_app.log"):
        os.remove("mock_app.log")