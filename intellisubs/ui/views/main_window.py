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
        self.grid_rowconfigure(1, weight=1) # For the text preview area

        # --- Top Controls Frame ---
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.controls_frame.grid_columnconfigure(1, weight=1) # Make file path entry expand

        self.file_label = ctk.CTkLabel(self.controls_frame, text="音频/视频文件:")
        self.file_label.grid(row=0, column=0, padx=(10,0), pady=10, sticky="w")

        self.file_path_var = ctk.StringVar()
        self.file_entry = ctk.CTkEntry(self.controls_frame, textvariable=self.file_path_var, width=300)
        self.file_entry.grid(row=0, column=1, padx=5, pady=10, sticky="ew")

        self.browse_button = ctk.CTkButton(self.controls_frame, text="选择文件", command=self.browse_file)
        self.browse_button.grid(row=0, column=2, padx=(0,10), pady=10, sticky="e")

        # Removed placeholder for status label in MainWindow, now in App.py
        # self.status_label = ctk.CTkLabel(self, text="状态: 就绪")
        # self.status_label.pack(pady=10)
        
        self.start_button = ctk.CTkButton(self.controls_frame, text="开始生成字幕", command=self.start_processing, state="disabled")
        self.start_button.grid(row=1, column=0, columnspan=3, padx=10, pady=(5,10), sticky="ew")

        # --- Settings Frame ---
        self.settings_frame = ctk.CTkFrame(self)
        self.settings_frame.grid(row=2, column=0, padx=10, pady=(0,10), sticky="ew")
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
        
        # --- Preview & Export Frame ---
        self.results_frame = ctk.CTkFrame(self)
        self.results_frame.grid(row=1, column=0, padx=10, pady=(0,10), sticky="nsew")
        self.results_frame.grid_columnconfigure(0, weight=1)
        self.results_frame.grid_rowconfigure(0, weight=1) # Make textbox expand

        self.preview_textbox = ctk.CTkTextbox(self.results_frame, wrap="word", state="disabled", height=200)
        self.preview_textbox.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        self.export_format_var = ctk.StringVar(value="SRT")
        self.export_options = ["SRT", "LRC", "ASS", "TXT"] # TXT for raw ASR output maybe
        self.export_menu = ctk.CTkOptionMenu(self.results_frame, variable=self.export_format_var, values=self.export_options)
        self.export_menu.grid(row=1, column=0, padx=5, pady=(5,10), sticky="w")
        
        self.export_button = ctk.CTkButton(self.results_frame, text="导出字幕", command=self.export_subtitles, state="disabled")
        self.export_button.grid(row=1, column=1, padx=5, pady=(5,10), sticky="e")
        
        # --- Settings Area (Placeholder) ---
        # self.settings_frame = ctk.CTkFrame(self, width=200) # Could be a right sidebar
        # self.settings_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="ns")
        # settings_label = ctk.CTkLabel(self.settings_frame, text="设置", font=ctk.CTkFont(size=16))
        # settings_label.pack(pady=10)
        # Add ASR model, device, LLM toggle, etc. here

        self.current_file_path = None
        self.generated_subtitle_data = None # To store the raw string from workflow manager

        self.toggle_llm_options_visibility() # Set initial visibility of LLM options

    def browse_file(self):
        file_types = [
            ("Audio/Video Files", "*.mp3 *.wav *.m4a *.mp4 *.mov *.mkv *.ogg"),
            ("All files", "*.*")
        ]
        path = filedialog.askopenfilename(title="选择音视频文件", filetypes=file_types)
        if path:
            self.current_file_path = path
            self.file_path_var.set(path)
            self.start_button.configure(state="normal")
            self.preview_textbox.configure(state="normal")
            self.preview_textbox.delete("1.0", "end")
            self.preview_textbox.insert("1.0", f"已选择文件: {path}\n点击“开始生成字幕”进行处理。")
            self.preview_textbox.configure(state="disabled")
            self.export_button.configure(state="disabled")
            self.generated_subtitle_data = None
            self.app.status_label.configure(text=f"状态: 已选择文件: {os.path.basename(path)}")
            self.logger.info(f"文件选择: {path}")

    def start_processing(self):
        if not self.current_file_path:
            messagebox.showerror("错误", "请先选择一个文件。")
            return

        self.start_button.configure(state="disabled")
        self.browse_button.configure(state="disabled")
        self.preview_textbox.configure(state="normal")
        self.preview_textbox.delete("1.0", "end")
        self.preview_textbox.insert("1.0", f"正在处理: {self.current_file_path}...\n请稍候。\n\n")
        self.preview_textbox.configure(state="disabled")
        self.app.status_label.configure(text=f"状态: 正在处理 {os.path.basename(self.current_file_path)}...")
        self.update_idletasks() # Ensure UI updates to show processing message
        self.logger.info(f"开始处理文件: {self.current_file_path}")

        # Call the workflow manager in a separate thread to prevent UI freeze
        self.start_button.configure(text="处理中...", state="disabled")
        self.export_button.configure(state="disabled")

        # Use a lambda to pass arguments to the threaded function
        import threading
        processing_thread = threading.Thread(target=self._run_processing_in_thread)
        processing_thread.start()
    
    def _run_processing_in_thread(self):
        try:
            # Get current settings from UI
            asr_model = self.asr_model_var.get()
            device = self.device_var.get()
            llm_enabled = self.llm_checkbox_var.get()
            llm_api_key = self.llm_api_key_var.get().strip() # Strip whitespace
            # Aggressively clean base_url: remove all whitespace characters (space, tab, newline, etc.)
            raw_llm_base_url = self.llm_base_url_var.get()
            llm_base_url = "".join(raw_llm_base_url.split()) if raw_llm_base_url else ""
            llm_model_name = self.llm_model_name_var.get().strip() # Strip whitespace

            # Update config manager with latest UI settings
            self.config["asr_model"] = asr_model
            self.config["device"] = device
            self.config["llm_enabled"] = llm_enabled
            self.config["llm_api_key"] = llm_api_key
            self.config["llm_base_url"] = llm_base_url if llm_base_url.strip() else None # Store None if empty
            self.config["llm_model_name"] = llm_model_name
            self.app.config_manager.save_config(self.config) # Save changes using the app's config_manager

            # Call the actual workflow manager
            self.logger.info(f"调用 WorkflowManager 处理文件: {self.current_file_path}, ASR模型: {asr_model}, 设备: {device}, LLM启用: {llm_enabled}, LLM模型: {llm_model_name if llm_enabled else 'N/A'}")
            
            # The workflow manager will return a structured data (e.g., list of subtitle objects)
            # and a preview string (e.g., SRT format for preview).
            # We will store the structured data and display the preview string.
            
            llm_params = None
            if llm_enabled:
                llm_params = {
                    "api_key": llm_api_key,
                    "base_url": self.config["llm_base_url"], # Use the possibly None value from config
                    "model_name": llm_model_name
                }

            preview_text, structured_subtitle_data = self.workflow_manager.process_audio_to_subtitle(
                audio_video_path=self.current_file_path,
                asr_model=asr_model,
                device=device,
                llm_enabled=llm_enabled,
                llm_params=llm_params, # Pass LLM specific params
                output_format="srt" # Default format for initial processing and preview
            )
            
            self.generated_subtitle_data = structured_subtitle_data # Store structured data
            status_msg = "处理完成！"
            result_data = preview_text

            self.preview_textbox.configure(state="normal")
            self.preview_textbox.insert("end", f"{status_msg}\n---\n")
            if result_data:
                self.preview_textbox.insert("end", result_data)
                self.export_button.configure(state="normal")
            else:
                self.preview_textbox.insert("end", "未能生成字幕数据。")
            self.preview_textbox.configure(state="disabled")
            self.app.status_label.configure(text=f"状态: {status_msg}")

        except Exception as e:
            messagebox.showerror("处理错误", f"生成字幕时发生错误: {e}")
            self.preview_textbox.configure(state="normal")
            self.preview_textbox.insert("end", f"\n错误: {e}")
            self.preview_textbox.configure(state="disabled")
            self.app.status_label.configure(text="状态: 处理失败")
            self.logger.exception(f"处理文件时发生错误: {e}")
        finally:
            self.start_button.configure(text="开始生成字幕", state="normal")
            self.browse_button.configure(state="normal")
            # Ensure any UI updates are done in the main thread
            self.app.after(0, lambda: self.app.status_label.configure(text=self.app.status_label.cget("text"))) # Refresh status


    def export_subtitles(self):
        if not self.generated_subtitle_data:
            messagebox.showwarning("无数据", "没有可导出的字幕数据。请先生成字幕。")
            return

        export_format = self.export_format_var.get().lower()
        
        # Determine initial filename based on original file and selected format
        base_name = os.path.splitext(os.path.basename(self.current_file_path))[0]
        default_filename = f"{base_name}.{export_format}"
        
        file_types_map = {
            "srt": [("SubRip Subtitle", "*.srt"), ("All files", "*.*")],
            "lrc": [("LyRiCs Subtitle", "*.lrc"), ("All files", "*.*")],
            "ass": [("Advanced SubStation Alpha", "*.ass"), ("All files", "*.*")],
            "txt": [("Text File", "*.txt"), ("All files", "*.*")]
        }
        file_types = file_types_map.get(export_format, [("All files", "*.*")]) # Fallback

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
                    self.generated_subtitle_data,
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
            
    def update_config(self, *args):
        """Updates the application configuration based on UI selections."""
        current_asr_model = self.asr_model_var.get()
        current_device = self.device_var.get()
        current_llm_enabled = self.llm_checkbox_var.get()
        current_llm_api_key = self.llm_api_key_var.get().strip() # Strip whitespace
        # Aggressively clean base_url: remove all whitespace characters
        raw_current_llm_base_url = self.llm_base_url_var.get()
        current_llm_base_url = "".join(raw_current_llm_base_url.split()) if raw_current_llm_base_url else ""
        current_llm_model_name = self.llm_model_name_var.get().strip() # Strip whitespace

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
        
        if changed:
            # Ensure self.config is the dict from the app instance if it's shared
            # Or if self.config is a direct reference to app.app_config, this is fine.
            # Assuming self.config is the actual config dictionary loaded by the app.
            self.app.config_manager.save_config(self.config)
            self.app.status_label.configure(text="状态: 配置已更新。")
        else:
            self.app.status_label.configure(text="状态: 配置未更改。")

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