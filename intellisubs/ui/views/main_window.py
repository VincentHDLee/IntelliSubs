# Main Window for IntelliSubs Application
import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import threading # For running processing in a separate thread
import logging # For the test __main__ logger

# Import component panels
from .main_window_components.top_controls_panel import TopControlsPanel
from .main_window_components.settings_panel import SettingsPanel
from .main_window_components.results_panel import ResultsPanel

# For testing standalone (if this file is run directly)
from ...utils.config_manager import ConfigManager
from ...utils.logger_setup import setup_logging
from ...core.workflow_manager import WorkflowManager


class MainWindow(ctk.CTkFrame):
    def __init__(self, master, config, workflow_manager, logger, **kwargs):
        super().__init__(master, **kwargs)
        self.app = master
        self.config = config
        self.workflow_manager = workflow_manager
        self.logger = logger

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Top Controls Panel (fixed height)
        self.grid_rowconfigure(1, weight=0)  # File List Frame (fixed height)
        self.grid_rowconfigure(2, weight=0)  # Settings Panel (can scroll internally if needed)
        self.grid_rowconfigure(3, weight=1)  # Results Panel (this one expands)

        # --- Instantiate Panels ---
        self.top_controls_panel = TopControlsPanel(
            self,
            app_ref=self.app,
            config=self.config,
            logger=self.logger,
            start_processing_callback=self.start_processing # Callback for start button
        )
        self.top_controls_panel.grid(row=0, column=0, padx=10, pady=(10,5), sticky="ew")

        # --- Selected Files List Frame ---
        self.file_list_frame = ctk.CTkFrame(self)
        self.file_list_frame.grid(row=1, column=0, padx=10, pady=(0,5), sticky="ew")
        self.file_list_frame.grid_columnconfigure(0, weight=1)
        self.file_list_frame.grid_rowconfigure(0, weight=1) # Allow textbox to expand if frame given weight

        self.selected_files_label = ctk.CTkLabel(self.file_list_frame, text="已选文件列表:")
        self.selected_files_label.grid(row=0, column=0, padx=(5,0), pady=(5,0), sticky="w")
        
        self.file_list_textbox = ctk.CTkTextbox(self.file_list_frame, wrap="none", height=100, state="disabled") # Height can be adjusted
        self.file_list_textbox.grid(row=1, column=0, padx=5, pady=5, sticky="ewns")
        # Consider making file_list_textbox shorter (e.g., height=80) if space is tight.

        self.settings_panel = SettingsPanel(
            self,
            app_ref=self.app,
            config=self.config,
            logger=self.logger,
            update_config_callback=self.update_config_from_panel # Pass callback
        )
        self.settings_panel.grid(row=2, column=0, padx=10, pady=(0,5), sticky="ew")
        
        self.results_panel = ResultsPanel(
            self,
            app_ref=self.app,
            logger=self.logger,
            workflow_manager=self.workflow_manager
        )
        self.results_panel.grid(row=3, column=0, padx=10, pady=(0,10), sticky="nsew")

        # --- State Variables ---
        self.selected_file_paths = []
        self.generated_subtitle_data_map = {}
        # self.current_previewing_file is primarily managed by ResultsPanel

    # --- Callback from TopControlsPanel ---
    def handle_file_selection_update(self, selected_paths):
        """Handles updates to file selection from TopControlsPanel."""
        self.selected_file_paths = selected_paths
        
        # Update displayed list of selected files
        self.file_list_textbox.configure(state="normal")
        self.file_list_textbox.delete("1.0", "end")
        if self.selected_file_paths:
            for f_path in self.selected_file_paths:
                self.file_list_textbox.insert("end", os.path.basename(f_path) + "\n")
        self.file_list_textbox.configure(state="disabled")

        # Reset internal data for processing results
        self.generated_subtitle_data_map = {}
        self.results_panel.set_generated_data(self.generated_subtitle_data_map)
        
        # Clear the visual list of processed results in ResultsPanel
        # This also clears the editor frame's current content by destroying widgets.
        self.results_panel.clear_result_list()
        
        # Explicitly set the editor to its default placeholder state.
        # ResultsPanel.set_main_preview_content(None) will display a generic message
        # like "Please select a processed file..." or "No file selected...".
        self.results_panel.set_main_preview_content(None)

        # The TopControlsPanel is responsible for updating its own start button state
        # via its browse_files -> update_start_button_state_based_on_files.
        # No direct call from here is needed if TopControlsPanel handles it.

        self.update_export_all_button_state() # Update export buttons based on new (empty) results

    def update_export_all_button_state(self):
        """ Centralized logic to update the 'Export All' button state via ResultsPanel. """
        output_dir = self.top_controls_panel.get_output_directory()
        
        # Check if there's any successfully generated data
        has_successful_results = False
        if self.generated_subtitle_data_map:
            for data in self.generated_subtitle_data_map.values():
                if data and isinstance(data, list) and len(data) > 0: # Assuming structured_subtitle_data is a list of segments
                    has_successful_results = True
                    break
                elif data and isinstance(data, dict) and data.get("segments"): # Alternative check for dict structure
                    has_successful_results = True
                    break

        can_export_all = bool(has_successful_results and \
                           output_dir and os.path.isdir(output_dir))
        
        can_export_current_flag = False
        if self.results_panel.current_previewing_file and \
           self.generated_subtitle_data_map.get(self.results_panel.current_previewing_file):
            # Check if the data for the current file is non-empty list/dict
            current_data = self.generated_subtitle_data_map[self.results_panel.current_previewing_file]
            if (isinstance(current_data, list) and len(current_data) > 0) or \
               (isinstance(current_data, dict) and current_data.get("segments")):
                can_export_current_flag = True
        
        self.results_panel.update_export_buttons_state(
            can_export_current=can_export_current_flag,
            can_export_all=can_export_all
        )


    # --- Processing Logic ---
    def start_processing(self):
        # selected_file_paths are now directly updated by handle_file_selection_update
        # and TopControlsPanel manages its own list.
        # We rely on self.selected_file_paths which should be in sync.
        if not self.selected_file_paths:
            messagebox.showerror("错误", "请先通过上方“浏览”按钮选择一个或多个文件。")
            return

        # Ensure TopControlsPanel UI is set for processing
        self.top_controls_panel.set_ui_for_processing(is_processing=True)

        self.app.status_label.configure(text=f"状态: 正在准备处理 {len(self.selected_file_paths)} 个文件...")
        self.results_panel.clear_result_list()
        self.results_panel.update_preview_for_status(f"开始处理 {len(self.selected_file_paths)} 个文件...\n请稍候。\n")
        
        self.update_idletasks() # Ensure UI updates before thread starts
        self.logger.info(f"准备开始批量处理 {len(self.selected_file_paths)} 个文件。")

        processing_thread = threading.Thread(target=self._run_processing_in_thread, daemon=True)
        processing_thread.start()

    def _run_processing_in_thread(self):
        try:
            ui_settings = self.settings_panel.get_settings()
            output_dir_to_use = self.top_controls_panel.get_output_directory()

            if output_dir_to_use and not os.path.isdir(output_dir_to_use):
                self.logger.warning(f"指定的输出目录 '{output_dir_to_use}' 不存在或不是一个目录。导出时将提示选择。")
            
            # Prepare config updates (but save them only if processing doesn't immediately fail)
            config_updates = {
                "asr_model": ui_settings["asr_model"],
                "device": ui_settings["device"],
                "language": ui_settings["language"],
                f"custom_dictionary_path_{ui_settings['language']}": ui_settings[f"custom_dictionary_path_{ui_settings['language']}"],
                "llm_enabled": ui_settings["llm_enabled"],
                "llm_api_key": ui_settings["llm_api_key"],
                "llm_base_url": ui_settings["llm_base_url"] if ui_settings["llm_base_url"] else None,
                "llm_model_name": ui_settings["llm_model_name"]
            }
            try:
                config_updates["min_duration_sec"] = float(ui_settings["min_duration_sec"])
            except ValueError:
                config_updates["min_duration_sec"] = 1.0
                self.logger.warning(f"无效最小显示时长: {ui_settings['min_duration_sec']}, 用默认值 {config_updates['min_duration_sec']}s")
            try:
                config_updates["min_gap_sec"] = float(ui_settings["min_gap_sec"])
            except ValueError:
                config_updates["min_gap_sec"] = 0.1
                self.logger.warning(f"无效最小间隔时长: {ui_settings['min_gap_sec']}, 用默认值 {config_updates['min_gap_sec']}s")

            if output_dir_to_use and os.path.isdir(output_dir_to_use):
                 config_updates["last_output_dir"] = output_dir_to_use
            
            # Apply and save config changes
            for key, value in config_updates.items():
                self.config[key] = value
            self.app.config_manager.save_config(self.config)
            self.logger.info("配置已从UI面板更新并保存。")

            self.generated_subtitle_data_map = {}
            self.results_panel.set_generated_data(self.generated_subtitle_data_map)

            # --- Batch Processing Logic ---
            processed_count = 0
            error_count = 0
            # self.generated_subtitle_data_map is already reset and passed to results_panel before the loop

            lang_code_for_dict_key = ui_settings['language'] # lang code for custom dict
            current_dict_path = ui_settings.get(f"custom_dictionary_path_{lang_code_for_dict_key}", "")

            for index, file_path in enumerate(self.selected_file_paths):
                base_filename = os.path.basename(file_path)
                status_prefix = f"处理中 ({index + 1}/{len(self.selected_file_paths)}): {base_filename}"
                self.logger.info(f"{status_prefix} ASR: {ui_settings['asr_model']}, LLM: {ui_settings['llm_enabled']}")
                
                self.app.after(0, lambda sp=status_prefix: self.app.status_label.configure(text=f"状态: {sp}"))
                self.app.after(0, lambda bn=base_filename: self.results_panel.update_preview_for_status(f"正在处理: {bn}...\n"))

                try:
                    llm_params = None
                    if ui_settings["llm_enabled"]:
                        llm_params = {
                            "api_key": ui_settings["llm_api_key"],
                            "base_url": self.config.get("llm_base_url"), # Use cleaned one from self.config
                            "model_name": ui_settings["llm_model_name"]
                        }

                    # Use min_duration_sec and min_gap_sec from self.config as they are validated
                    preview_text, structured_subtitle_data = self.workflow_manager.process_audio_to_subtitle(
                        audio_video_path=file_path,
                        asr_model=ui_settings["asr_model"],
                        device=ui_settings["device"],
                        llm_enabled=ui_settings["llm_enabled"],
                        llm_params=llm_params,
                        output_format="srt",
                        current_custom_dict_path=current_dict_path,
                        processing_language=ui_settings["language"],
                        min_duration_sec=self.config["min_duration_sec"],
                        min_gap_sec=self.config["min_gap_sec"]
                    )
                    
                    self.generated_subtitle_data_map[file_path] = structured_subtitle_data
                    # self.results_panel.set_generated_data(self.generated_subtitle_data_map) # Already set, map is updated by ref
                    
                    self.app.after(0, lambda p=file_path, s_data=structured_subtitle_data, pt=preview_text, success=True, err_msg=None:
                                   self.results_panel.add_result_entry(p, s_data, pt, success, err_msg))
                    
                    processed_count += 1
                    self.logger.info(f"文件 {base_filename} 处理成功。")

                except Exception as e_file:
                    error_count += 1
                    self.logger.error(f"处理文件 {base_filename} 时发生错误: {e_file}", exc_info=True)
                    self.app.after(0, lambda p=file_path, success=False, err_msg=str(e_file):
                                   self.results_panel.add_result_entry(p, None, None, success, err_msg))
            
            final_status_msg = f"批量处理完成: {processed_count} 个成功, {error_count} 个失败。"
            self.logger.info(final_status_msg)
            self.app.after(0, lambda: self.app.status_label.configure(text=f"状态: {final_status_msg}"))
            
            if processed_count > 0:
                if self.selected_file_paths:
                    # Try to find the first successfully processed file to preview
                    first_successful_path = None
                    for fp_candidate in self.selected_file_paths:
                        if fp_candidate in self.generated_subtitle_data_map and self.generated_subtitle_data_map[fp_candidate]:
                            first_successful_path = fp_candidate
                            break
                    
                    if first_successful_path:
                        first_preview_text = self.workflow_manager.export_subtitles(
                            self.generated_subtitle_data_map[first_successful_path], "srt"
                        )
                        self.app.after(0, lambda: self.results_panel.set_main_preview_content(first_preview_text, first_successful_path))
                    elif error_count == len(self.selected_file_paths): # All failed
                         self.app.after(0, lambda: self.results_panel.update_preview_for_status("所有文件处理失败或未生成有效字幕。\n请检查日志获取详情。"))
                    else: # Some processed, some failed, but none of the first ones were successful
                        self.app.after(0, lambda: self.results_panel.update_preview_for_status(f"{processed_count} 个文件处理完成，部分可能包含错误。\n请查看结果列表。"))

            elif error_count > 0 : # No successes, only errors
                self.app.after(0, lambda: self.results_panel.update_preview_for_status("所有文件处理失败。\n请检查日志获取详情。"))
            else: # No files processed (e.g. if selected_file_paths was empty, though guarded)
                self.app.after(0, lambda: self.results_panel.update_preview_for_status("未处理任何文件。\n"))

            self.app.after(0, self.update_export_all_button_state)

        except Exception as e_batch:
            self.logger.exception(f"批量处理时发生意外错误: {e_batch}")
            self.app.after(0, lambda eb=e_batch: messagebox.showerror("批量处理错误", f"批量处理时发生意外错误: {eb}"))
            self.app.after(0, lambda: self.app.status_label.configure(text="状态: 批量处理失败"))
            self.app.after(0, lambda eb=e_batch: self.results_panel.update_preview_for_status(f"\n批量处理错误: {eb}\n请检查日志。"))
        finally:
            self.app.after(0, lambda: self.top_controls_panel.set_ui_for_processing(is_processing=False))
            # Start button state within TopControlsPanel should be managed based on file selection state
            self.app.after(0, self.top_controls_panel.update_start_button_state_based_on_files)
            
            # Ensure status label reflects the final state without overwriting detailed error messages
            current_status = self.app.status_label.cget("text")
            if "批量处理完成" not in current_status and "批量处理失败" not in current_status :
                 self.app.after(0, lambda: self.app.status_label.configure(text=f"状态: 操作结束。"))


    # --- Config Update Callback for SettingsPanel ---
    def update_config_from_panel(self, *args):
        """
        Called by SettingsPanel when a setting is changed.
        This method centralizes saving the config.
        """
        ui_settings = self.settings_panel.get_settings()
        changed_keys = []

        def update_if_changed(key, new_value, is_sensitive=False):
            nonlocal changed_keys
            old_value = self.config.get(key)
            if old_value != new_value:
                self.config[key] = new_value
                if not is_sensitive:
                    changed_keys.append(f"{key}: '{old_value}' -> '{new_value}'")
                else:
                    changed_keys.append(f"{key} changed")
                return True
            return False

        update_if_changed("asr_model", ui_settings["asr_model"])
        update_if_changed("device", ui_settings["device"])
        current_language = ui_settings["language"]
        update_if_changed("language", current_language)
        
        lang_dict_key = f"custom_dictionary_path_{current_language}"
        update_if_changed(lang_dict_key, ui_settings.get(lang_dict_key, ""))

        update_if_changed("llm_enabled", ui_settings["llm_enabled"])
        update_if_changed("llm_api_key", ui_settings["llm_api_key"], is_sensitive=True)
        
        cleaned_base_url = ui_settings["llm_base_url"] if ui_settings["llm_base_url"] else None
        update_if_changed("llm_base_url", cleaned_base_url)
        update_if_changed("llm_model_name", ui_settings["llm_model_name"])
        
        try:
            min_dur = float(ui_settings["min_duration_sec"])
            update_if_changed("min_duration_sec", min_dur)
        except ValueError:
            self.logger.warning(f"更新配置时，无效的最小显示时长: {ui_settings['min_duration_sec']}")
        try:
            min_gap = float(ui_settings["min_gap_sec"])
            update_if_changed("min_gap_sec", min_gap)
        except ValueError:
            self.logger.warning(f"更新配置时，无效的最小间隔时长: {ui_settings['min_gap_sec']}")

        if changed_keys:
            self.app.config_manager.save_config(self.config)
            self.logger.info(f"配置已通过设置面板更新并保存。更改项: {'; '.join(changed_keys)}")
            self.app.status_label.configure(text="状态: 配置已更新。")
        else:
            self.app.status_label.configure(text="状态: 配置无变化。")


    # --- Export related methods called by ResultsPanel ---
    def export_single_file(self, file_path_to_export, subtitle_data_or_text_to_export, export_format):
        """
        Handles exporting a single file's subtitles.
        `subtitle_data_or_text_to_export` can be structured data or pre-formatted text (from preview).
        """
        self.logger.info(f"MainWindow: 接到导出单个文件请求 for '{file_path_to_export}', 格式: {export_format}")
        
        if not file_path_to_export or subtitle_data_or_text_to_export is None :
            self.logger.error("导出单个文件错误: 文件路径或字幕数据为空。")
            messagebox.showerror("导出错误", "无法导出，缺少文件信息或字幕内容。")
            return

        base_name_for_output = os.path.splitext(os.path.basename(file_path_to_export))[0]
        export_format_lower = str(export_format).lower() if export_format else "srt"
        default_filename = f"{base_name_for_output}.{export_format_lower}"
        
        file_types_map = {
            "srt": [("SubRip Subtitle", "*.srt"), ("All files", "*.*")],
            "lrc": [("LyRiCs Subtitle", "*.lrc"), ("All files", "*.*")],
            "ass": [("Advanced SubStation Alpha", "*.ass"), ("All files", "*.*")],
            "txt": [("Text File", "*.txt"), ("All files", "*.*")]
        }
        file_types = file_types_map.get(export_format_lower, [("All files", "*.*")])

        chosen_output_dir = self.top_controls_panel.get_output_directory()
        
        initial_dir_fd = os.path.dirname(file_path_to_export)
        if chosen_output_dir and os.path.isdir(chosen_output_dir):
            initial_dir_fd = chosen_output_dir
        elif self.config.get("last_output_dir") and os.path.isdir(self.config.get("last_output_dir")):
            initial_dir_fd = self.config.get("last_output_dir")

        save_path = filedialog.asksaveasfilename(
            master=self.app,
            title=f"导出为 {export_format_lower.upper()}",
            initialfile=default_filename,
            initialdir=initial_dir_fd,
            defaultextension=f".{export_format_lower}",
            filetypes=file_types
        )

        if save_path:
            try:
                final_data_to_save = ""
                if isinstance(subtitle_data_or_text_to_export, str):
                    final_data_to_save = subtitle_data_or_text_to_export
                elif isinstance(subtitle_data_or_text_to_export, (list, dict)):
                    final_data_to_save = self.workflow_manager.export_subtitles(
                        subtitle_data_or_text_to_export, export_format_lower
                    )
                else:
                    self.logger.error(f"导出错误: 不支持的字幕数据类型 {type(subtitle_data_or_text_to_export)}")
                    raise ValueError("无效的字幕数据格式用于导出。")

                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(final_data_to_save)
                
                new_output_dir = os.path.dirname(save_path)
                if new_output_dir != self.config.get("last_output_dir"):
                    self.config["last_output_dir"] = new_output_dir
                    self.app.config_manager.save_config(self.config)
                    self.top_controls_panel.set_output_directory_text(new_output_dir)
                    self.logger.info(f"最后输出目录已更新为: {new_output_dir}")

                messagebox.showinfo("成功", f"字幕已导出到:\n{save_path}")
                self.app.status_label.configure(text=f"状态: 已导出到 {os.path.basename(save_path)}")
                self.logger.info(f"字幕成功导出到: {save_path}")

            except Exception as e:
                self.logger.exception(f"导出字幕 '{save_path}' 时发生错误: {e}")
                messagebox.showerror("导出错误", f"导出字幕时发生错误:\n{e}")
                self.app.status_label.configure(text="状态: 导出失败")
        else:
            self.logger.info("单个文件导出操作已取消。")
            self.app.status_label.configure(text="状态: 导出已取消。")


    def export_all_successful_subtitles_from_results_panel(self, export_format):
        """Handles exporting all successful subtitles, called by ResultsPanel."""
        self.logger.info(f"MainWindow: 接到批量导出请求, 格式: {export_format}")
        
        export_format_lower = str(export_format).lower() if export_format else "srt"

        successful_items = {}
        for fp, data in self.generated_subtitle_data_map.items():
            if data and ((isinstance(data, list) and len(data) > 0) or \
                         (isinstance(data, dict) and data.get("segments"))):
                 successful_items[fp] = data
                 
        if not successful_items:
            messagebox.showwarning("无数据", "没有成功处理的字幕可供导出。")
            self.app.status_label.configure(text="状态: 无成功结果可导出。")
            return

        output_dir = self.top_controls_panel.get_output_directory()
        if not output_dir or not os.path.isdir(output_dir):
            messagebox.showwarning("选择目录", "请先在上方“输出目录”选择一个有效的目录用于批量导出。")
            output_dir = filedialog.askdirectory(master=self.app, title="选择批量导出目录")
            if not output_dir:
                self.logger.info("批量导出操作已取消（未选择目录）。")
                self.app.status_label.configure(text="状态: 批量导出已取消。")
                return
            self.top_controls_panel.set_output_directory_text(output_dir)
            self.config["last_output_dir"] = output_dir
            self.app.config_manager.save_config(self.config)


        exported_count = 0
        error_count = 0
        
        self.results_panel.update_export_buttons_state(is_processing=True) # Let ResultsPanel manage its own buttons
        self.app.status_label.configure(text=f"状态: 正在批量导出 {len(successful_items)} 个文件...")
        self.update_idletasks()

        self.logger.info(f"开始批量导出所有成功字幕到目录: {output_dir}, 格式: {export_format_lower.upper()}")

        for file_path, subtitle_data in successful_items.items():
            try:
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                output_filename = f"{base_name}.{export_format_lower}"
                full_save_path = os.path.join(output_dir, output_filename)

                formatted_string = self.workflow_manager.export_subtitles(
                    subtitle_data, export_format_lower
                )
                with open(full_save_path, 'w', encoding='utf-8') as f:
                    f.write(formatted_string)
                self.logger.info(f"成功导出: {base_name} -> {output_filename}")
                exported_count += 1
            except Exception as e:
                self.logger.error(f"导出文件 {os.path.basename(file_path)} 时发生错误: {e}", exc_info=True)
                error_count += 1
        
        self.results_panel.update_export_buttons_state(is_processing=False) # Reset buttons in panel
        self.update_export_all_button_state() # Update MainWindow's overall perspective

        summary_message = f"批量导出完成: {exported_count} 个成功。"
        if error_count > 0:
            summary_message += f" {error_count} 个失败。"
        
        messagebox.showinfo("批量导出完成", summary_message)
        self.app.status_label.configure(text=f"状态: {summary_message}")
        self.logger.info(summary_message)

# For testing MainWindow independently
if __name__ == '__main__':
    class MockApp(ctk.CTk): # Used for standalone testing
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.title("MainWindow Test (Refactored)")
            self.geometry("950x750")
            
            test_config_path = "mock_config_main_window_refactored.json"
            test_log_path = "mock_app_main_window_refactored.log"

            self.config_manager = ConfigManager(test_config_path)
            self.app_config = self.config_manager.load_config()
            self.app_config.setdefault("last_output_dir", "")
            self.app_config.setdefault("asr_model", "small")
            self.app_config.setdefault("device", "cpu")
            self.app_config.setdefault("language", "ja")
            # ... other essential configs

            self.logger = setup_logging(log_file=test_log_path, level="DEBUG")
            self.workflow_manager = WorkflowManager(config=self.app_config, logger=self.logger)
            
            self.status_label = ctk.CTkLabel(self, text="Mock Status: 就绪")
            self.status_label.pack(side="bottom", fill="x", padx=10, pady=5)

    app_test = MockApp()
    main_frame = MainWindow(master=app_test, config=app_test.app_config,
                            workflow_manager=app_test.workflow_manager, logger=app_test.logger)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    app_test.mainloop()

    # Clean up mock config and log files
    if os.path.exists(app_test.config_manager.config_file):
        os.remove(app_test.config_manager.config_file)
    
    log_file_handler = next((h for h in app_test.logger.handlers if isinstance(h, logging.FileHandler)), None)
    if log_file_handler:
        log_file_path_to_remove = log_file_handler.baseFilename
        log_file_handler.close()
        app_test.logger.removeHandler(log_file_handler)
        if os.path.exists(log_file_path_to_remove):
            os.remove(log_file_path_to_remove)
        os.remove("mock_app.log")