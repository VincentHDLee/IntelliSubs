import customtkinter as ctk
from tkinter import filedialog
import os

class SettingsPanel(ctk.CTkFrame):
    def __init__(self, master, app_ref, config, logger, update_config_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app_ref # Reference to the main IntelliSubsApp instance
        self.config = config
        self.logger = logger
        self.update_config_callback = update_config_callback

        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.pack(expand=True, fill="both", padx=0, pady=0) # Use pack for the tab view itself
        
        self.main_settings_tab = self.tab_view.add("主要设置")
        self.ai_settings_tab = self.tab_view.add("AI 及高级设置")

        # Configure columns for tabs
        self.main_settings_tab.grid_columnconfigure((0,1,2,3), weight=1)
        self.ai_settings_tab.grid_columnconfigure((0,1,2,3), weight=1)

        self._create_main_settings_widgets()
        self._create_ai_settings_widgets()
        
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


    def _create_ai_settings_widgets(self):
        # --- LLM Checkbox ---
        self.llm_checkbox_var = ctk.BooleanVar(value=self.config.get("llm_enabled", False))
        self.llm_checkbox = ctk.CTkCheckBox(self.ai_settings_tab, text="启用LLM增强", variable=self.llm_checkbox_var, command=self.toggle_llm_options_and_update_config)
        self.llm_checkbox.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="w")

        # --- LLM Specific Settings ---
        self.llm_settings_frame = ctk.CTkFrame(self.ai_settings_tab)
        self.llm_settings_frame.grid(row=1, column=0, columnspan=4, padx=5, pady=(0,5), sticky="ew")
        self.llm_settings_frame.grid_columnconfigure(1, weight=1)

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
        
        # Bind focus out to trigger config update for text entries
        self.llm_api_key_entry.bind("<FocusOut>", lambda e: self.update_config_callback())
        self.llm_base_url_entry.bind("<FocusOut>", lambda e: self.update_config_callback())
        self.llm_model_name_entry.bind("<FocusOut>", lambda e: self.update_config_callback())


        # --- Intelligent Timeline Adjustment Settings ---
        self.timeline_adj_label = ctk.CTkLabel(self.ai_settings_tab, text="智能时间轴调整:", font=ctk.CTkFont(weight="bold"))
        self.timeline_adj_label.grid(row=2, column=0, columnspan=4, padx=10, pady=(10,0), sticky="w")

        self.min_duration_var = ctk.StringVar(value=str(self.config.get("min_duration_sec", "1.0")))
        self.min_duration_label = ctk.CTkLabel(self.ai_settings_tab, text="最小显示时长 (秒):")
        self.min_duration_label.grid(row=3, column=0, padx=(10,5), pady=5, sticky="w")
        self.min_duration_entry = ctk.CTkEntry(self.ai_settings_tab, textvariable=self.min_duration_var, width=60)
        self.min_duration_entry.grid(row=3, column=1, padx=(0,10), pady=5, sticky="w")
        self.min_duration_entry.bind("<FocusOut>", lambda e: self.update_config_callback())

        self.min_gap_var = ctk.StringVar(value=str(self.config.get("min_gap_sec", "0.1")))
        self.min_gap_label = ctk.CTkLabel(self.ai_settings_tab, text="最小间隔时长 (秒):")
        self.min_gap_label.grid(row=3, column=2, padx=(10,5), pady=5, sticky="w")
        self.min_gap_entry = ctk.CTkEntry(self.ai_settings_tab, textvariable=self.min_gap_var, width=60)
        self.min_gap_entry.grid(row=3, column=3, padx=(0,10), pady=5, sticky="w")
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
        else:
            self.llm_settings_frame.grid_remove() # Hide frame

    def toggle_llm_options_and_update_config(self, *args):
        """Called when the LLM checkbox state changes."""
        self.toggle_llm_options_visibility()
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
            "min_duration_sec": self.min_duration_var.get(),
            "min_gap_sec": self.min_gap_var.get(),
        }
        return settings