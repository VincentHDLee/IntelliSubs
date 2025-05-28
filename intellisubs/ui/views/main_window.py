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
from .main_window_components.combined_file_status_panel import CombinedFileStatusPanel

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

        # Configure MainWindow grid (2 columns, 1 row)
        self.grid_columnconfigure(0, weight=1)  # Left controls column
        self.grid_columnconfigure(1, weight=3)  # Right info/edit column (more space)
        self.grid_rowconfigure(0, weight=1)     # Single row that expands vertically

        # --- Create Left Controls Frame ---
        self.left_controls_frame = ctk.CTkFrame(self)
        self.left_controls_frame.grid(row=0, column=0, padx=(10,5), pady=10, sticky="nsew")
        self.left_controls_frame.grid_columnconfigure(0, weight=1)
        self.left_controls_frame.grid_rowconfigure(0, weight=0)  # TopControlsPanel (compact)
        self.left_controls_frame.grid_rowconfigure(1, weight=1)  # SettingsPanel (can expand or fixed)

        # --- Create Right Info/Edit Frame ---
        self.right_info_edit_frame = ctk.CTkFrame(self)
        self.right_info_edit_frame.grid(row=0, column=1, padx=(5,10), pady=10, sticky="nsew")
        self.right_info_edit_frame.grid_columnconfigure(0, weight=1)
        self.right_info_edit_frame.grid_rowconfigure(0, weight=1)  # Row for CombinedFileStatusPanel (some expansion)
        self.right_info_edit_frame.grid_rowconfigure(1, weight=2)  # Row for Subtitle Editor (more expansion)
        self.right_info_edit_frame.grid_rowconfigure(2, weight=0)  # Row for Export Controls (fixed height)

        # --- Instantiate Panels ---
        # Top Controls Panel (in left_controls_frame, row 0)
        self.top_controls_panel = TopControlsPanel(
            self.left_controls_frame,
            app_ref=self.app,
            config=self.config,
            logger=self.logger,
            start_processing_callback=self.start_processing,
            main_window_ref=self
        )
        self.top_controls_panel.grid(row=0, column=0, padx=0, pady=(0,5), sticky="ew") # Compact, fill width

        # Settings Panel (in left_controls_frame, row 1)
        self.settings_panel = SettingsPanel(
            self.left_controls_frame,
            app_ref=self.app,
            config=self.config,
            logger=self.logger,
            update_config_callback=self.update_config_from_panel
        )
        self.settings_panel.grid(row=1, column=0, padx=0, pady=(5,0), sticky="nsew") # Fill remaining space

        # --- Create frames within right_info_edit_frame ---

        # Combined File Status Panel (in right_info_edit_frame, row 0)
        self.combined_file_status_panel = CombinedFileStatusPanel(
            self.right_info_edit_frame,
            logger=self.logger
        )
        self.combined_file_status_panel.grid(row=0, column=0, padx=0, pady=(0,5), sticky="nsew")

        # Instantiate ResultsPanel
        # actual_master_for_list_frame is None as this is handled by CombinedFileStatusPanel
        self.results_panel_handler = ResultsPanel(
            master=self,
            actual_master_for_list_frame=None,
            actual_master_for_editor_frame=self.right_info_edit_frame,
            actual_master_for_export_frame=self.right_info_edit_frame,
            app_ref=self.app,
            logger=self.logger,
            workflow_manager=self.workflow_manager
        )
        
        # Subtitle Editor (child of right_info_edit_frame, gridded into it by MainWindow)
        self.results_panel_handler.subtitle_editor_scrollable_frame.grid(row=1, column=0, padx=0, pady=(0,5), sticky="nsew")

        # Export Controls (child of right_info_edit_frame, gridded into it by MainWindow)
        self.results_panel_handler.export_controls_frame.grid(row=2, column=0, padx=0, pady=0, sticky="ew")

        # --- State Variables ---
        self.selected_file_paths = []
        self.generated_subtitle_data_map = {}
        # self.current_previewing_file is primarily managed by ResultsPanel

    # --- Callback from TopControlsPanel ---
    def handle_file_selection_update(self, selected_paths):
        """Handles updates to file selection from TopControlsPanel."""
        self.selected_file_paths = selected_paths
        
        # Update the new combined panel
        self.combined_file_status_panel.clear_files()
        if self.selected_file_paths:
            for f_path in self.selected_file_paths:
                self.combined_file_status_panel.add_file(f_path)
        
        # Reset internal data for processing results
        self.generated_subtitle_data_map = {}
        # Pass the map to results_panel_handler if it still needs it for editor context
        if hasattr(self.results_panel_handler, 'set_generated_data'):
            self.results_panel_handler.set_generated_data(self.generated_subtitle_data_map)
        
        # Clear the editor frame's current content.
        # The clear_result_list method in ResultsPanel should now primarily focus on clearing editor state.
        if hasattr(self.results_panel_handler, 'clear_result_list') and self.results_panel_handler.result_list_scrollable_frame is None:
             self.results_panel_handler.clear_result_list() # Call if it's adapted for editor only
        else: # Fallback or if clear_result_list was too broad
            self.results_panel_handler.set_main_preview_content(None) # Ensure editor is cleared

        # Explicitly set the editor to its default placeholder state.
        self.results_panel_handler.set_main_preview_content(None)

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
        
        if has_successful_results and not (output_dir and os.path.isdir(output_dir)):
            self.logger.info("UpdateExportAllButtonState: '导出所有成功' 按钮保持禁用，因为输出目录未设置或无效，即使存在成功的结果。")
            if not output_dir:
                self.app.status_label.configure(text="状态: 请设置输出目录以启用批量导出。")
            elif not os.path.isdir(output_dir):
                self.app.status_label.configure(text=f"状态: 输出目录 '{output_dir}' 无效。")

        can_export_current_flag = False
        can_insert_item_flag = bool(self.results_panel_handler.current_previewing_file) # Can insert if a file is previewing

        if self.results_panel_handler.current_previewing_file:
            current_preview_data = self.generated_subtitle_data_map.get(self.results_panel_handler.current_previewing_file)
            if current_preview_data and \
               ((isinstance(current_preview_data, list) and len(current_preview_data) > 0) or \
                (isinstance(current_preview_data, dict) and current_preview_data.get("segments"))):
                can_export_current_flag = True
            
            if not can_export_current_flag : # Has preview file, but no data to export
                 self.logger.info("UpdateExportAllButtonState: '导出当前预览' 按钮禁用，因为当前预览文件无有效字幕数据。")
                 # Status bar might be set by can_insert_item_flag logic if no preview file
                 if can_insert_item_flag: # Has preview, but no data.
                      self.app.status_label.configure(text="状态: 当前预览无字幕数据可导出。")

        if not can_insert_item_flag: # No file is being previewed at all
            self.logger.info("UpdateExportAllButtonState: '导出当前预览' 和 '插入新行' 按钮禁用，因为没有文件正在预览。")
            self.app.status_label.configure(text="状态: 请预览文件以进行编辑或导出当前。")
        
        self.results_panel_handler.update_export_buttons_state(
            can_export_current=can_export_current_flag,
            can_export_all=can_export_all,
            can_insert_item=can_insert_item_flag
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
        # Editor area might show a general "processing" message or be cleared by set_main_preview_content(None)
        self.results_panel_handler.set_main_preview_content(None)
        # Consider a more specific placeholder for editor during batch processing later if needed.
        
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
    
            self.generated_subtitle_data_map = {} # This map is still crucial for holding processed data
            if hasattr(self.results_panel_handler, 'set_generated_data'): # Update editor's view of the data map
                self.results_panel_handler.set_generated_data(self.generated_subtitle_data_map)
    
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
                
                self.app.after(0, lambda p=file_path: self.combined_file_status_panel.update_file_status(p, "处理中..."))
                self.app.after(0, lambda sp=status_prefix: self.app.status_label.configure(text=f"状态: {sp}"))

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
                    # Call the new handler for successful processing
                    self.app.after(0, lambda p=file_path, s_data=structured_subtitle_data:
                                   self.handle_processing_success_for_combined_panel(p, s_data))
                    
                    processed_count += 1
                    self.logger.info(f"文件 {base_filename} 处理成功。")

                except Exception as e_file:
                    error_count += 1
                    self.logger.error(f"处理文件 {base_filename} 时发生错误: {e_file}", exc_info=True)
                    # Update CombinedFileStatusPanel with error
                    self.app.after(0, lambda p=file_path, err=str(e_file):
                                   self.combined_file_status_panel.update_file_status(p, "错误", error_message=err, processing_done=True))
            
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
                        # first_preview_text is no longer needed here as ResultsPanel.set_main_preview_content
                        # now takes file_path and fetches structured data internally to populate the editor.
                        # first_preview_text = self.workflow_manager.export_subtitles(
                        #     self.generated_subtitle_data_map[first_successful_path], "srt"
                        # )
                        self.app.after(0, lambda path=first_successful_path: self.results_panel_handler.set_main_preview_content(path)) # This part is still valid for editor
                    elif error_count == len(self.selected_file_paths): # All failed
                         self.app.after(0, lambda: self.results_panel_handler.set_main_preview_content(None)) # Clear editor
                         # Status updates handled by combined_panel
                    else: # Some processed, some failed, but none of the first ones were successful for preview
                        self.app.after(0, lambda: self.results_panel_handler.set_main_preview_content(None)) # Clear editor

            elif error_count > 0 : # No successes, only errors
                self.app.after(0, lambda: self.results_panel_handler.set_main_preview_content(None)) # Clear editor
            else: # No files processed
                self.app.after(0, lambda: self.results_panel_handler.set_main_preview_content(None)) # Clear editor

            self.app.after(0, self.update_export_all_button_state)

        except Exception as e_batch:
            self.logger.exception(f"批量处理时发生意外错误: {e_batch}")
            self.app.after(0, lambda eb=e_batch: messagebox.showerror("批量处理错误", f"批量处理时发生意外错误: {eb}"))
            self.app.after(0, lambda: self.app.status_label.configure(text="状态: 批量处理失败"))
            self.app.after(0, lambda: self.results_panel_handler.set_main_preview_content(None)) # Clear editor
        finally:
            self.app.after(0, lambda: self.top_controls_panel.set_ui_for_processing(is_processing=False))
            # Start button state within TopControlsPanel should be managed based on file selection state
            self.app.after(0, self.top_controls_panel.update_start_button_state_based_on_files)
            
            # Ensure status label reflects the final state without overwriting detailed error messages
            current_status = self.app.status_label.cget("text")
            if "批量处理完成" not in current_status and "批量处理失败" not in current_status :
                 self.app.after(0, lambda: self.app.status_label.configure(text=f"状态: 操作结束。"))


    def handle_processing_success_for_combined_panel(self, file_path, structured_data):
        """Handles UI updates in CombinedFileStatusPanel after a file is successfully processed."""
        self.combined_file_status_panel.update_file_status(file_path, "完成", processing_done=True)
        if structured_data: # Ensure there's data to preview and enable button
            self.combined_file_status_panel.set_preview_button_callback(
                file_path,
                lambda p=file_path: self.results_panel_handler.set_main_preview_content(p)
            )
        self.update_export_all_button_state() # Update export buttons as results come in

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
            self.app.status_label.configure(text="状态: 请选择批量导出目录。") # Update status before dialog
            output_dir = filedialog.askdirectory(master=self.app, title="选择批量导出目录")
            if not output_dir:
                self.logger.info("批量导出操作已取消（未选择目录）。")
                self.app.status_label.configure(text="状态: 批量导出已取消。")
                return
            self.top_controls_panel.set_output_directory_text(output_dir) # Update the text field in TopControlsPanel
            self.config["last_output_dir"] = output_dir # Save to config
            self.app.config_manager.save_config(self.config)


        exported_count = 0
        error_count = 0
        
        # Manually disable relevant buttons in ResultsPanel during batch export
        if hasattr(self.results_panel_handler, 'export_button'):
            self.results_panel_handler.export_button.configure(state="disabled")
        if hasattr(self.results_panel_handler, 'export_all_button'):
            self.results_panel_handler.export_all_button.configure(state="disabled")
        if hasattr(self.results_panel_handler, 'apply_changes_button'):
            self.results_panel_handler.apply_changes_button.configure(state="disabled")
        if hasattr(self.results_panel_handler, 'insert_item_button'): # If this button exists
            self.results_panel_handler.insert_item_button.configure(state="disabled")

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
        
        # Re-enable buttons based on current state by calling MainWindow's central update method
        self.update_export_all_button_state()

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