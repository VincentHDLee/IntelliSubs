import customtkinter as ctk
from tkinter import filedialog
import os
import threading # For running async tasks without blocking UI
import asyncio   # For running the async method from WorkflowManager
# from tkinter import messagebox # Or use CTkMessagebox if available and preferred

class SettingsPanel(ctk.CTkFrame):
    def __init__(self, master, app_ref, config, logger, update_config_callback, main_window_ref, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app_ref # Reference to the main IntelliSubsApp instance
        self.main_window_ref = main_window_ref # Reference to the MainWindow instance
        self.config = config
        self.logger = logger
        self.update_config_callback = update_config_callback
        self.imported_script_path = None # For storing path of imported script
        self.imported_script_content = None # For storing content of imported script

        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.pack(expand=True, fill="both", padx=0, pady=0) # Use pack for the tab view itself
        
        self.main_settings_tab = self.tab_view.add("主要设置")
        self.ai_settings_tab = self.tab_view.add("AI 设置") # Renamed
        self.advanced_settings_tab = self.tab_view.add("高级设置") # New tab

        # Configure columns for tabs
        self.main_settings_tab.grid_columnconfigure((0,1,2,3), weight=1)
        self.ai_settings_tab.grid_columnconfigure((0,1,2,3), weight=1)
        self.advanced_settings_tab.grid_columnconfigure((0,1,2,3), weight=1) # Configure new tab

        self._create_main_settings_widgets()
        self._create_ai_specific_settings_widgets() # Renamed method
        self._create_advanced_settings_widgets()   # New method for advanced settings
        
        self.toggle_llm_options_visibility() # Set initial visibility

    def _create_main_settings_widgets(self):
        # --- ASR Model and Device ---
        self.asr_model_label = ctk.CTkLabel(self.main_settings_tab, text="ASR模型:")
        self.asr_model_label.grid(row=0, column=0, padx=(10,5), pady=5, sticky="w")
        self.asr_model_var = ctk.StringVar(value=self.config.get("asr_model", "small"))
        self.asr_model_options = ["tiny", "base", "small", "medium", "large"]
        self.asr_model_menu = ctk.CTkOptionMenu(self.main_settings_tab, variable=self.asr_model_var, values=self.asr_model_options, command=self.update_config_callback)
        self.asr_model_menu.grid(row=0, column=1, padx=(0,10), pady=5, sticky="ew")

        self.device_label = ctk.CTkLabel(self.main_settings_tab, text="处理设备:")
        self.device_label.grid(row=0, column=2, padx=(10,5), pady=5, sticky="w")
        self.device_var = ctk.StringVar(value=self.config.get("device", "cpu"))
        self.device_options = ["cpu", "cuda", "mps"] # TODO: Dynamically check availability
        self.device_menu = ctk.CTkOptionMenu(self.main_settings_tab, variable=self.device_var, values=self.device_options, command=self.update_config_callback)
        self.device_menu.grid(row=0, column=3, padx=(0,10), pady=5, sticky="ew")

        # --- Language Selection ---
        self.language_label = ctk.CTkLabel(self.main_settings_tab, text="处理语言:")
        self.language_label.grid(row=2, column=0, padx=(10,5), pady=5, sticky="w")
        
        self.language_var = ctk.StringVar(value=self.config.get("language", "ja")) # Stores the code e.g. "ja"
        self.language_map = {"ja": "日本語 (Japanese)", "zh": "中文 (Chinese)", "en": "English"} # TODO: Externalize this
        self.language_display_options = list(self.language_map.values())
        
        current_lang_code = self.language_var.get()
        current_display_language = self.language_map.get(current_lang_code, current_lang_code)
        self.language_menu_display_var = ctk.StringVar(value=current_display_language) # For OptionMenu

        self.language_menu = ctk.CTkOptionMenu(
            self.main_settings_tab,
            variable=self.language_menu_display_var,
            values=self.language_display_options,
            command=self.on_language_selected_ui # Calls internal handler first
        )
        self.language_menu.grid(row=2, column=1, padx=(0,10), pady=5, sticky="ew")

        # --- Custom Dictionary Path Setting ---
        self.custom_dict_label = ctk.CTkLabel(self.main_settings_tab, text="自定义词典 (CSV/TXT):")
        self.custom_dict_label.grid(row=1, column=0, padx=(10,5), pady=5, sticky="w")
        
        dict_config_key = f"custom_dictionary_path_{current_lang_code}"
        self.custom_dict_path_var = ctk.StringVar(value=self.config.get(dict_config_key, ""))
        
        self.custom_dict_entry = ctk.CTkEntry(self.main_settings_tab, textvariable=self.custom_dict_path_var) # command=self.update_config_callback ? No, on browse
        self.custom_dict_entry.grid(row=1, column=1, columnspan=2, padx=(0,5), pady=5, sticky="ew")

        self.custom_dict_browse_button = ctk.CTkButton(self.main_settings_tab, text="浏览...", command=self.browse_custom_dictionary_file, fg_color="#449D44")
        self.custom_dict_browse_button.grid(row=1, column=3, padx=(0,10), pady=5, sticky="e")


    def _create_ai_specific_settings_widgets(self): # Renamed method
        # --- LLM Checkbox ---
        self.llm_checkbox_var = ctk.BooleanVar(value=self.config.get("llm_enabled", False))
        self.llm_checkbox = ctk.CTkCheckBox(self.ai_settings_tab, text="启用LLM增强", variable=self.llm_checkbox_var, command=self.toggle_llm_options_and_update_config)
        self.llm_checkbox.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.import_script_button = ctk.CTkButton(self.ai_settings_tab, text="导入剧本", width=100, command=self._browse_script_file)
        self.import_script_button.grid(row=0, column=1, padx=(0,5), pady=5, sticky="w")

        self.script_status_label = ctk.CTkLabel(self.ai_settings_tab, text="剧本: 未导入", anchor="w", wraplength=180) # Anchor w to align left
        self.script_status_label.grid(row=0, column=2, padx=(0,5), pady=5, sticky="ew")
        
        self.clear_script_button = ctk.CTkButton(self.ai_settings_tab, text="清除", width=60, command=self._clear_imported_script)
        self.clear_script_button.grid(row=0, column=3, padx=(0,10), pady=5, sticky="e")


        # --- LLM Specific Settings ---
        self.llm_settings_frame = ctk.CTkFrame(self.ai_settings_tab)
        self.llm_settings_frame.grid(row=1, column=0, columnspan=4, padx=5, pady=(0,5), sticky="ew")
        self.llm_settings_frame.grid_columnconfigure(1, weight=1) # For entry/combobox
        self.llm_settings_frame.grid_columnconfigure(2, weight=0) # For refresh button
        self.llm_settings_frame.grid_columnconfigure(3, weight=0) # For test button


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
        
        self.llm_model_name_label = ctk.CTkLabel(self.llm_settings_frame, text="选择LLM模型:") # Changed Label
        self.llm_model_name_label.grid(row=2, column=0, padx=(5,5), pady=5, sticky="w")
        
        current_model_name = self.config.get("llm_model_name", "")
        self.llm_model_name_var = ctk.StringVar(value=current_model_name) # This will hold the selected/typed value
        
        # Store the full list of models fetched from the server
        self.full_llm_models_list = []
        if self.app and hasattr(self.app, 'workflow_manager'):
            self.full_llm_models_list = self.app.workflow_manager.available_llm_models # Initialize if already fetched

        # Initial values for ComboBox: Use current config value or placeholder
        initial_combobox_values = [current_model_name] if current_model_name and current_model_name in self.full_llm_models_list else []
        if not initial_combobox_values and self.full_llm_models_list: # If current_model_name is not in full list (e.g. stale config), use full list
            initial_combobox_values = self.full_llm_models_list
        elif not initial_combobox_values and not self.full_llm_models_list : # No models fetched yet
             initial_combobox_values = ["点击右侧按钮刷新"]
             if not current_model_name and self.llm_checkbox_var.get():
                 self.llm_model_name_var.set("点击右侧按钮刷新") # Set var for placeholder
             elif current_model_name : # if there is a config name but no list
                 initial_combobox_values = [current_model_name]


        self.llm_model_name_combobox = ctk.CTkComboBox(
            self.llm_settings_frame,
            variable=self.llm_model_name_var,
            values=initial_combobox_values,
            command=self._on_llm_model_selected_from_combobox # Update config on selection from dropdown or Enter
        )
        self.llm_model_name_combobox.grid(row=2, column=1, padx=(0,5), pady=5, sticky="ew") # Adjusted columnspan
        # Bind KeyRelease to filter models as user types
        self.llm_model_name_combobox.bind("<KeyRelease>", self._filter_llm_models_on_input)
        # Also bind FocusOut to save any typed value that wasn't selected via command
        self.llm_model_name_combobox.bind("<FocusOut>", lambda e: self.update_config_callback())

        self.llm_refresh_models_button = ctk.CTkButton(
            self.llm_settings_frame,
            text="刷新",
            width=55, # Slightly smaller width
            command=self.fetch_llm_models_for_ui
        )
        self.llm_refresh_models_button.grid(row=2, column=2, padx=(0,5), pady=5, sticky="e") # New column

        self.llm_test_connection_button = ctk.CTkButton(
            self.llm_settings_frame,
            text="测试",
            width=55, # Slightly smaller width
            command=self._test_llm_connection
        )
        self.llm_test_connection_button.grid(row=2, column=3, padx=(0,5), pady=5, sticky="e") # New column
        
        # --- System Prompt ---
        self.llm_system_prompt_label = ctk.CTkLabel(self.llm_settings_frame, text="System Prompt:")
        self.llm_system_prompt_label.grid(row=3, column=0, padx=(5,5), pady=5, sticky="nw") # sticky "nw" for top-left alignment of label
        
        self.llm_system_prompt_var = ctk.StringVar(value=self.config.get("llm_system_prompt", ""))
        self.llm_system_prompt_textbox = ctk.CTkTextbox(
            self.llm_settings_frame,
            height=80, # Adjust height as needed
            wrap="word" # Wrap text at word boundaries
        )
        self.llm_system_prompt_textbox.grid(row=3, column=1, columnspan=3, padx=(0,5), pady=5, sticky="ew")
        self.llm_system_prompt_textbox.insert("0.0", self.llm_system_prompt_var.get()) # Load initial value
        # Bind FocusOut to update the variable and then the config
        self.llm_system_prompt_textbox.bind("<FocusOut>", self._on_system_prompt_changed)

        # Bind focus out to trigger config update for text entries
        # and potentially refresh models if relevant fields (API key, Base URL) change.
        self.llm_api_key_entry.bind("<FocusOut>", lambda e: self._on_llm_param_changed())
        self.llm_base_url_entry.bind("<FocusOut>", lambda e: self._on_llm_param_changed())
        
        # Attempt to fetch models on init if LLM is enabled
        if self.llm_checkbox_var.get():
             self.after(150, self.fetch_llm_models_for_ui) # Slight delay

    def _on_system_prompt_changed(self, event=None):
        """Called when the system prompt textbox loses focus."""
        new_prompt_content = self.llm_system_prompt_textbox.get("0.0", "end-1c") # Get all text minus trailing newline
        self.llm_system_prompt_var.set(new_prompt_content)
        self.logger.debug(f"SettingsPanel: System prompt changed. Length: {len(new_prompt_content)}")
        self.update_config_callback()

    def _create_advanced_settings_widgets(self):
        # --- Intelligent Timeline Adjustment Settings ---
        self.timeline_adj_label = ctk.CTkLabel(self.advanced_settings_tab, text="智能时间轴调整:", font=ctk.CTkFont(weight="bold"))
        self.timeline_adj_label.grid(row=0, column=0, columnspan=4, padx=10, pady=(10,0), sticky="w")

        self.min_duration_var = ctk.StringVar(value=str(self.config.get("min_duration_sec", "1.0")))
        self.min_duration_label = ctk.CTkLabel(self.advanced_settings_tab, text="最小显示时长 (秒):")
        self.min_duration_label.grid(row=1, column=0, padx=(10,5), pady=5, sticky="w")
        self.min_duration_entry = ctk.CTkEntry(self.advanced_settings_tab, textvariable=self.min_duration_var, width=60)
        self.min_duration_entry.grid(row=1, column=1, padx=(0,10), pady=5, sticky="w")
        self.min_duration_entry.bind("<FocusOut>", lambda e: self.update_config_callback())

        self.min_gap_var = ctk.StringVar(value=str(self.config.get("min_gap_sec", "0.1")))
        self.min_gap_label = ctk.CTkLabel(self.advanced_settings_tab, text="最小间隔时长 (秒):")
        self.min_gap_label.grid(row=1, column=2, padx=(10,5), pady=5, sticky="w")
        self.min_gap_entry = ctk.CTkEntry(self.advanced_settings_tab, textvariable=self.min_gap_var, width=60)
        self.min_gap_entry.grid(row=1, column=3, padx=(0,10), pady=5, sticky="w")
        self.min_gap_entry.bind("<FocusOut>", lambda e: self.update_config_callback())

    def on_language_selected_ui(self, selected_display_name: str):
        """Handles language selection from the OptionMenu and updates related UI."""
        selected_lang_code = "ja" # Default
        for code, display_name in self.language_map.items():
            if display_name == selected_display_name:
                selected_lang_code = code
                break
        
        self.language_var.set(selected_lang_code) # Update the actual variable holding the code
        
        # Update custom dictionary path entry for the new language
        new_dict_config_key = f"custom_dictionary_path_{selected_lang_code}"
        self.custom_dict_path_var.set(self.config.get(new_dict_config_key, ""))
        
        self.logger.info(f"UI: 语言选择更改为: {selected_lang_code} ({selected_display_name}). 自定义词典路径已更新。")
        # Now call the main update_config callback to persist all changes
        self.update_config_callback()


    def browse_custom_dictionary_file(self):
        file_types = [("CSV files", "*.csv"), ("Text files", "*.txt"), ("All files", "*.*")]
        current_path = self.custom_dict_path_var.get()
        initial_dir = os.path.dirname(current_path) if current_path and os.path.exists(current_path) else os.getcwd()
        
        selected_path = filedialog.askopenfilename(
            title="选择自定义词典文件",
            filetypes=file_types,
            initialdir=initial_dir
        )
        if selected_path:
            self.custom_dict_path_var.set(selected_path)
            self.logger.info(f"UI: 自定义词典文件选择: {selected_path} for language {self.language_var.get()}")
            # Call the main update_config callback to persist this change
            self.update_config_callback()

    def toggle_llm_options_visibility(self):
        if self.llm_checkbox_var.get():
            self.llm_settings_frame.grid() # Make frame visible
            self.import_script_button.grid()
            self.script_status_label.grid()
            self.clear_script_button.grid()
        else:
            self.llm_settings_frame.grid_remove() # Hide frame
            self.import_script_button.grid_remove()
            self.script_status_label.grid_remove()
            self.clear_script_button.grid_remove()

    def toggle_llm_options_and_update_config(self, *args):
        """Called when the LLM checkbox state changes."""
        llm_is_now_enabled = self.llm_checkbox_var.get()
        self.toggle_llm_options_visibility()
        
        if llm_is_now_enabled:
            # If LLM is enabled, and base URL is present, try to fetch models.
            # This gives immediate feedback if the user enables LLM with a URL already set.
            base_url = self.llm_base_url_var.get().strip()
            if base_url:
                self.logger.info("LLM enabled with Base URL present, auto-fetching models.")
                # Use self.after to ensure this runs after the current event processing
                self.after(50, self.fetch_llm_models_for_ui)
            else:
                # If LLM enabled but no base URL, prompt user or set dropdown to a specific state.
                self.llm_model_name_combobox.configure(values=["请填写Base URL并刷新"]) # Update ComboBox
                self.llm_model_name_var.set("请填写Base URL并刷新")
        else:
            # LLM is disabled, clear/reset the model dropdown
            self.logger.info("LLM disabled, resetting model dropdown.")
            self.llm_model_name_combobox.configure(values=["LLM已禁用"]) # Update ComboBox
            self.llm_model_name_var.set("LLM已禁用")
            self.full_llm_models_list = [] # Clear local cache of full models
            # Also clear any stored available_llm_models in workflow_manager if desired,
            # though this might be better handled by workflow_manager itself if config changes.
            if self.app and hasattr(self.app, 'workflow_manager'):
                self.app.workflow_manager.available_llm_models = []


        self.update_config_callback() # Then update and save the config

    def get_settings(self):
        """Returns a dictionary of the current settings from the UI."""
        settings = {
            "asr_model": self.asr_model_var.get(),
            "device": self.device_var.get(),
            "language": self.language_var.get(), # Actual language code
            # Custom dict path is for the currently selected language
            f"custom_dictionary_path_{self.language_var.get()}": self.custom_dict_path_var.get().strip(),
            "llm_enabled": self.llm_checkbox_var.get(),
            "llm_api_key": self.llm_api_key_var.get().strip(),
            "llm_base_url": "".join(self.llm_base_url_var.get().split()) if self.llm_base_url_var.get() else "", # Cleaned
            "llm_model_name": self.llm_model_name_var.get().strip(),
            "llm_system_prompt": self.llm_system_prompt_var.get().strip(), # Added system prompt
            "min_duration_sec": self.min_duration_var.get(),
            "min_gap_sec": self.min_gap_var.get(),
            "llm_script_context": self.imported_script_content if self.imported_script_content else ""
        }
        return settings

    def _browse_script_file(self):
        file_types = [("Text files", "*.txt"), ("Markdown files", "*.md"), ("All files", "*.*")]
        # Use last_output_dir from config as initialdir if available, else cwd
        initial_dir = self.config.get("last_output_dir", os.getcwd())

        selected_path = filedialog.askopenfilename(
            title="选择剧本文件",
            filetypes=file_types,
            initialdir=initial_dir
        )
        if selected_path:
            try:
                with open(selected_path, 'r', encoding='utf-8') as f:
                    # Limit script content for now to avoid issues, can be configured later
                    # For example, read up to ~10000 characters as a safety measure
                    # This limit should ideally be configurable or handled more gracefully in LLMEnhancer
                    # For now, let's not limit here, but be mindful for LLMEnhancer
                    content = f.read()
                
                self.imported_script_path = selected_path
                self.imported_script_content = content # Store content
                script_filename = os.path.basename(selected_path)
                self.script_status_label.configure(text=f"剧本: {script_filename}")
                self.logger.info(f"UI: 剧本文件已导入: {selected_path}. 内容长度: {len(content)}")
                self.update_config_callback() # To save if script context were part of config, or signal change
            except Exception as e:
                self.logger.error(f"UI: 读取剧本文件失败 '{selected_path}': {e}")
                self.script_status_label.configure(text="剧本: 读取失败")
                self.imported_script_path = None
                self.imported_script_content = None
                if hasattr(self.app, 'show_status_message'):
                    self.app.show_status_message(f"读取剧本失败: {e}", error=True)
        else:
            self.logger.info("UI: 未选择剧本文件。")

    def _clear_imported_script(self):
        self.imported_script_path = None
        self.imported_script_content = None
        self.script_status_label.configure(text="剧本: 未导入")
        self.logger.info("UI: 已清除导入的剧本。")
        self.update_config_callback() # To reflect change if script context was part of config

    def _on_llm_param_changed(self):
        """Called when API key or Base URL text entries lose focus."""
        self.logger.debug("SettingsPanel: LLM API Key or Base URL changed by user.")
        self.update_config_callback() # Save the changes first
        # Optionally, you might want to auto-trigger a model refresh here,
        # or inform the user that they might need to refresh.
        # For now, we rely on the manual refresh button.
        # Example: if self.llm_checkbox_var.get():
        # self.fetch_llm_models_for_ui() # This might be too aggressive.

    def fetch_llm_models_for_ui(self):
        """
        Initiates fetching of LLM models and updates the UI dropdown.
        This version runs the async operation in a separate thread.
        """
        if not self.app or not hasattr(self.app, 'workflow_manager'):
            self.logger.error("WorkflowManager not available via app_ref.")
            if hasattr(self.app, 'show_status_message'):
                self.app.show_status_message("内部错误: WorkflowManager 不可用", error=True)
            return

        if not self.llm_checkbox_var.get():
            self.logger.info("LLM is disabled, skipping model fetch.")
            # Reset dropdown to a sensible state if LLM is off
            self.llm_model_name_combobox.configure(values=["LLM已禁用"]) # Update ComboBox
            self.llm_model_name_var.set("LLM已禁用")
            self.full_llm_models_list = []
            return

        self.logger.info("UI: Initiating LLM model fetch...")
        self.llm_refresh_models_button.configure(state="disabled", text="刷新中...")
        
        current_model_selection = self.llm_model_name_var.get()
        # Handle placeholder texts if they are current selection
        if current_model_selection in ["LLM已禁用", "刷新中...", "点击右侧按钮刷新", "请填写Base URL并刷新", "无可用模型", "获取失败"]:
            current_model_selection = "" # Clear placeholder to attempt restoring a real model if available

        self.llm_model_name_combobox.configure(values=["刷新中..."]) # Update ComboBox
        self.llm_model_name_var.set("刷新中...")

        # Prepare config for WorkflowManager using current UI values
        current_ui_llm_config = {
            "llm_base_url": self.llm_base_url_var.get().strip(),
            "llm_api_key": self.llm_api_key_var.get().strip(),
            "language": self.language_var.get()
        }

        thread = threading.Thread(
            target=self._fetch_models_thread_target,
            args=(current_ui_llm_config, current_model_selection),
            daemon=True
        )
        thread.start()

    def _fetch_models_thread_target(self, llm_config_for_fetch: dict, previous_selection: str):
        """
        Worker function executed in a separate thread to call the async model fetching.
        """
        self.logger.debug(f"Thread target: Fetching models with config: {llm_config_for_fetch}")
        models = []
        error_msg = None
        try:
            # Each thread needs its own event loop for asyncio.run()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            models = loop.run_until_complete(
                self.app.workflow_manager.async_get_llm_models(current_llm_config=llm_config_for_fetch)
            )
        except RuntimeError as e:
             if "cannot be called from a running event loop" in str(e):
                self.logger.error("RuntimeError: async_get_llm_models cannot be called from a running event loop in this thread context. This needs careful handling of asyncio loops per thread.", exc_info=True)
                error_msg = "事件循环错误"
                # This case is tricky. For simplicity, we'll report error.
                # A more robust solution might involve a single, managed asyncio event loop for background tasks.
             else:
                self.logger.error(f"RuntimeError during model fetch: {e}", exc_info=True)
                error_msg = f"运行时错误: {e}"
        except Exception as e:
            self.logger.error(f"Exception during model fetch: {e}", exc_info=True)
            error_msg = f"获取失败: {e}"
        finally:
            if 'loop' in locals() and not loop.is_closed(): # Ensure loop is defined and not closed
                loop.close()
            # Schedule UI update back on the main thread using self.after
            self.after(0, self._update_llm_model_dropdown, models, previous_selection, error_msg)

    def _update_llm_model_dropdown(self, models: list[str], previous_selection: str, error_message: str = None):
        """
        Updates the LLM model dropdown. This method MUST be called from the main UI thread (e.g., via self.after).
        """
        self.llm_refresh_models_button.configure(state="normal", text="刷新") # Re-enable button

        if error_message:
            self.logger.error(f"UI: Error updating LLM models dropdown: {error_message}")
            # Try to restore previous selection or show error in dropdown
            fallback_value = previous_selection if previous_selection and \
                               previous_selection not in ["刷新中...", "LLM已禁用", "点击右侧按钮刷新", "请填写Base URL并刷新", "无可用模型"] \
                               else "获取失败"
            self.llm_model_name_combobox.configure(values=[fallback_value]) # Update ComboBox
            self.llm_model_name_var.set(fallback_value)
            if hasattr(self.app, 'show_status_message'):
                self.app.show_status_message(f"获取模型列表失败: {error_message[:100]}", error=True, duration_ms=5000)
            self.full_llm_models_list = [] # Clear local cache
            return

        self.full_llm_models_list = models # Store the full list
        
        if models:
            self.logger.info(f"UI: Successfully fetched models. Updating ComboBox with {len(models)} models.")
            self.llm_model_name_combobox.configure(values=models) # Update ComboBox
            
            current_input = self.llm_model_name_combobox.get() # Preserve user's typed input if any
            if current_input and current_input not in ["刷新中...", "点击右侧按钮刷新"] and any(m.lower().startswith(current_input.lower()) for m in models):
                 # If user was typing something and it's a prefix of a model, keep it and filter
                 self._filter_llm_models_on_input() # This will update var if exact match
                 # Check if var was set by filter; if not, and previous_selection is valid, use it
                 if self.llm_model_name_var.get() in ["刷新中...", "点击右侧按钮刷新"]: # Var not set by filter
                    if previous_selection in models:
                        self.llm_model_name_var.set(previous_selection)
                    elif models:
                        self.llm_model_name_var.set(models[0]) # Default to first model
            elif previous_selection in models:
                self.llm_model_name_var.set(previous_selection)
            elif models: # If previous selection not in new list, select the first one
                self.llm_model_name_var.set(models[0])
            else: # Should not be reached if models is True, but for safety
                self.llm_model_name_var.set("") # No models, clear selection
        else:
            self.logger.warning("UI: No LLM models returned after fetch (list is empty).")
            current_config_model = self.config.get("llm_model_name", "")
            display_values = [current_config_model] if current_config_model else ["无可用模型"]
            display_selection = current_config_model if current_config_model else "无可用模型"
            
            self.llm_model_name_combobox.configure(values=display_values) # Update ComboBox
            self.llm_model_name_var.set(display_selection)
            if hasattr(self.app, 'show_status_message'):
                 self.app.show_status_message("未能获取到模型列表，请检查Base URL或API Key后重试。", warning=True, duration_ms=5000)
        
        self.update_config_callback() # Save potentially new selection

    def _filter_llm_models_on_input(self, event=None):
        """Filters the ComboBox dropdown based on user input."""
        current_input = self.llm_model_name_var.get().lower() # CTkComboBox variable updates on input
        if not self.full_llm_models_list:
            # If full list isn't populated (e.g., fetch failed or not run),
            # or if input is a placeholder, don't filter.
            # Allow refresh button to be the primary way to populate initially.
            if current_input in ["刷新中...", "点击右侧按钮刷新", "请填写base url并刷新", "无可用模型", "llm已禁用", "获取失败"]:
                 return
            # If user types when list is empty, show "no models" or similar.
            self.llm_model_name_combobox.configure(values=["无可用模型 (请刷新)"])
            return

        if not current_input: # If input is empty, show all models
            self.llm_model_name_combobox.configure(values=self.full_llm_models_list)
            return

        filtered_models = [
            model for model in self.full_llm_models_list
            if current_input in model.lower() # Simple substring matching
        ]

        if filtered_models:
            self.llm_model_name_combobox.configure(values=filtered_models)
            # If the current input is an exact match for one of the filtered models,
            # ensure the variable reflects this specific choice (CTkComboBox might do this already).
            # If current input exactly matches a model, CTkComboBox var should be that model.
            # If not, var remains the typed input.
        else:
            self.llm_model_name_combobox.configure(values=["无匹配模型"])
        
        # Note: The self.llm_model_name_var is already updated by CTkComboBox as the user types.
        # The command callback or FocusOut will handle saving the final selected/typed value.

    def _on_llm_model_selected_from_combobox(self, selected_value: str):
        """Callback when a model is selected from ComboBox dropdown or Enter is pressed."""
        # The variable self.llm_model_name_var is already updated to selected_value by CTkComboBox.
        # We just need to ensure the config is saved.
        self.logger.debug(f"LLM Model selected/entered via ComboBox: {selected_value}")
        # If user selected a placeholder like "无匹配模型", don't save that as actual model name
        if selected_value in ["无匹配模型", "无可用模型 (请刷新)", "刷新中...", "点击右侧按钮刷新", "请填写Base URL并刷新", "LLM已禁用", "获取失败"]:
            # Optionally, clear the variable or revert to a previous valid one if desired,
            # but for now, let FocusOut handle saving whatever is in the var.
            # Or, prevent these from being actual "selectable" items if ComboBox allows.
            # For now, we'll rely on FocusOut to save the typed text if it's not a real selection.
            return
        self.update_config_callback()

    def _test_llm_connection(self):
        """Initiates a test of the LLM connection via the app_ref (MainWindow)."""
        if not self.llm_checkbox_var.get():
            if hasattr(self.app, 'show_status_message'): # Check if app_ref is valid and has the method
                self.app.show_status_message("请先启用LLM增强复选框以进行测试。", warning=True, duration_ms=3000)
            else: # Fallback if show_status_message is not available on app (e.g. during early init or testing)
                self.logger.warning("SettingsPanel: LLM is not enabled, cannot test connection. (show_status_message unavailable)")
            return

        if self.main_window_ref and hasattr(self.main_window_ref, 'request_llm_test_connection'):
            # MainWindow's request_llm_test_connection will fetch settings from this panel directly.
            self.logger.info("SettingsPanel: Requesting LLM connection test via MainWindow instance.")
            self.main_window_ref.request_llm_test_connection()
        else:
            has_callback = False
            main_window_ref_type_str = "None"
            if self.main_window_ref:
                main_window_ref_type_str = str(type(self.main_window_ref))
                has_callback = hasattr(self.main_window_ref, 'request_llm_test_connection')
            
            self.logger.error(f"SettingsPanel: Cannot test LLM connection. main_window_ref type is {main_window_ref_type_str}, hasattr(request_llm_test_connection): {has_callback}.")
            
            # Try to show message via app_ref if main_window_ref is the issue, or log if app_ref also problematic
            if hasattr(self.app, 'show_status_message'):
                self.app.show_status_message("内部错误: 无法执行LLM连接测试 (ref error)。", error=True, duration_ms=3000)
            else:
                # This critical log might be redundant if the error above gives enough info, but keep for now.
                self.logger.critical(f"SettingsPanel: LLM test failed. main_window_ref type: {main_window_ref_type_str}, app_ref type: {type(self.app)}.")