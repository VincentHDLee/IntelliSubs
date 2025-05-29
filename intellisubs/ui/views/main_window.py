# Main Window for IntelliSubs Application
import customtkinter as ctk
import json
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
            update_config_callback=self.update_config_from_panel,
            main_window_ref=self # Pass a reference to MainWindow itself
        )
        self.settings_panel.grid(row=1, column=0, padx=0, pady=(5,0), sticky="nsew") # Fill remaining space

        # --- Create frames within right_info_edit_frame ---

        # Combined File Status Panel (in right_info_edit_frame, row 0)
        self.combined_file_status_panel = CombinedFileStatusPanel(
            self.right_info_edit_frame,
            logger=self.logger,
            app_ref=self, # Pass app_ref
            on_file_removed_callback=self.handle_file_removed_from_panel
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

        # --- Timeout and pending operation flags ---
        # Check if pending_llm_enhancements already exists from a previous partial application
        if not hasattr(self, 'pending_llm_enhancements'):
            self.pending_llm_enhancements = {}
        self.llm_enhancement_timeout_ms = 60000  # 60 seconds for LLM enhancement
        if not hasattr(self, '_llm_enhancement_after_ids'): # Check before initializing
            self._llm_enhancement_after_ids = {} # Stores .after() IDs for cancellation {file_path: after_id}

        if not hasattr(self, 'llm_test_pending_id'): # Check before initializing
            self.llm_test_pending_id = None # Stores .after() ID for LLM test connection
        self.llm_test_timeout_ms = 30000   # 30 seconds for LLM test connection
        if not hasattr(self, 'llm_test_pending'): # Check before initializing
            self.llm_test_pending = False # Flag for actual pending LLM test curl command


    # --- Callback from TopControlsPanel ---
    def handle_file_selection_update(self, new_selected_paths):
        """
        Handles updates to file selection from TopControlsPanel.
        Manages adding new files to the UI and data maps, and removing deselected ones,
        while preserving data for files that remain selected.
        """
        self.logger.info(f"Handling file selection update. New selection has {len(new_selected_paths)} files.")
        
        previous_ui_files = set(self.combined_file_status_panel.get_all_file_paths())
        current_selected_set = set(new_selected_paths)

        # Add new files to UI:
        # These are files in the new selection that were not previously in the UI.
        files_to_add_to_ui = current_selected_set - previous_ui_files
        if files_to_add_to_ui:
            self.logger.info(f"Adding {len(files_to_add_to_ui)} new files to UI: {files_to_add_to_ui}")
            for f_path_add in files_to_add_to_ui:
                self.combined_file_status_panel.add_file(f_path_add)
        else:
            self.logger.info("No new files to add to UI.")

        # Remove deselected files from UI:
        # These are files that were in the UI but are no longer in the new selection.
        # Calling _remove_file_entry will trigger the on_file_removed_callback (handle_file_removed_from_panel),
        # which should handle removing the file from self.selected_file_paths (the main list in MainWindow,
        # though it will be overridden shortly) and self.generated_subtitle_data_map.
        files_to_remove_from_ui = previous_ui_files - current_selected_set
        if files_to_remove_from_ui:
            self.logger.info(f"Removing {len(files_to_remove_from_ui)} deselected files from UI: {files_to_remove_from_ui}")
            for f_path_remove in files_to_remove_from_ui:
                self.combined_file_status_panel._remove_file_entry(f_path_remove)
                # Note: self.generated_subtitle_data_map is handled by the callback
        else:
            self.logger.info("No files to remove from UI.")

        # Update MainWindow's master list of selected files to the new state.
        # This must happen AFTER determining files to add/remove based on comparison with previous UI state.
        self.selected_file_paths = list(new_selected_paths)
        self.logger.info(f"MainWindow selected_file_paths updated. Count: {len(self.selected_file_paths)}")

        # Update editor state
        if not self.selected_file_paths: # No files selected at all
            self.results_panel_handler.set_main_preview_content(None)
            self.logger.info("Editor cleared as no files are selected.")
        elif self.results_panel_handler.current_previewing_file and \
             self.results_panel_handler.current_previewing_file not in current_selected_set:
            # If the file that was being previewed is no longer in the selection, clear the editor.
            self.logger.info(f"Previously previewed file '{self.results_panel_handler.current_previewing_file}' "
                             "is no longer selected. Clearing editor.")
            self.results_panel_handler.set_main_preview_content(None)
        
        # Ensure the ResultsPanel's internal data map reference is correct,
        # though it's more about the content of the map being up-to-date.
        if hasattr(self.results_panel_handler, 'set_generated_data'):
            self.results_panel_handler.set_generated_data(self.generated_subtitle_data_map)

        self.update_export_all_button_state()
        # TopControlsPanel is responsible for updating its own start button state.

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
                "llm_model_name": ui_settings["llm_model_name"],
                "llm_system_prompt": ui_settings.get("llm_system_prompt", "") # Added system prompt
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
                
                self.app.after(0, lambda p=file_path: self.combined_file_status_panel.update_file_status(p, CombinedFileStatusPanel.STATUS_PROCESSING_ASR))
                self.app.after(0, lambda sp=status_prefix: self.app.status_label.configure(text=f"状态: {sp}"))

                try:
                    llm_params = None
                    if ui_settings["llm_enabled"]:
                        llm_params = {
                            "api_key": ui_settings["llm_api_key"],
                            "base_url": self.config.get("llm_base_url"), # Use cleaned one from self.config
                            "model_name": ui_settings["llm_model_name"],
                            "system_prompt": ui_settings.get("llm_system_prompt", "") # Pass system_prompt
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
                                   self.combined_file_status_panel.update_file_status(p, CombinedFileStatusPanel.STATUS_ERROR, error_message=err, processing_done=True))
            
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


    def handle_file_removed_from_panel(self, file_path_removed: str):
        """Callback when a file is removed from the CombinedFileStatusPanel."""
        if file_path_removed in self.selected_file_paths:
            self.selected_file_paths.remove(file_path_removed)
            self.logger.info(f"File removed from selection via panel: {file_path_removed}")

        if file_path_removed in self.generated_subtitle_data_map:
            del self.generated_subtitle_data_map[file_path_removed]
            self.logger.info(f"Removed generated data for: {file_path_removed}")

        # Update TopControlsPanel display if it shows file count
        if hasattr(self.top_controls_panel, 'update_file_path_display'):
            self.top_controls_panel.update_file_path_display(num_files=len(self.selected_file_paths))
        
        # If the removed file was being previewed, clear the editor
        if self.results_panel_handler.current_previewing_file == file_path_removed:
            self.results_panel_handler.set_main_preview_content(None)
            self.logger.info(f"Cleared preview as removed file {file_path_removed} was being previewed.")

        self.update_export_all_button_state()
        self.top_controls_panel.update_start_button_state_based_on_files() # Update start button too

    def handle_file_removed_from_panel(self, file_path_removed: str):
        """Callback when a file is removed from the CombinedFileStatusPanel."""
        if file_path_removed in self.selected_file_paths:
            self.selected_file_paths.remove(file_path_removed)
            self.logger.info(f"File removed from selection via panel: {file_path_removed}")

        if file_path_removed in self.generated_subtitle_data_map:
            del self.generated_subtitle_data_map[file_path_removed]
            self.logger.info(f"Removed generated data for: {file_path_removed}")

        # Update TopControlsPanel display if it shows file count
        if hasattr(self.top_controls_panel, 'update_file_path_display'):
            self.top_controls_panel.update_file_path_display(num_files=len(self.selected_file_paths))
        
        # If the removed file was being previewed, clear the editor
        if self.results_panel_handler.current_previewing_file == file_path_removed:
            self.results_panel_handler.set_main_preview_content(None)
            self.logger.info(f"Cleared preview as removed file {file_path_removed} was being previewed.")

        self.update_export_all_button_state()
        # Also update the start button state in TopControlsPanel as the number of files changed
        if hasattr(self.top_controls_panel, 'update_start_button_state_based_on_files'):
            self.top_controls_panel.update_start_button_state_based_on_files()

    def handle_processing_success_for_combined_panel(self, file_path, structured_data):
        """Handles UI updates in CombinedFileStatusPanel after a file is successfully ASR processed."""
        self.combined_file_status_panel.update_file_status(file_path, CombinedFileStatusPanel.STATUS_ASR_DONE, processing_done=True)
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
        update_if_changed("llm_system_prompt", ui_settings.get("llm_system_prompt", "")) # Added system prompt
        
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

    def request_llm_enhancement_for_file(self, file_path: str):
        """Handles the request to LLM enhance a specific file using curl."""
        self.logger.info(f"LLM增强请求: {file_path}")

        if not file_path in self.generated_subtitle_data_map or not self.generated_subtitle_data_map[file_path]:
            self.logger.error(f"无法为 {file_path} 执行LLM增强: 未找到原始ASR字幕数据。")
            self.combined_file_status_panel.update_file_status(file_path, CombinedFileStatusPanel.STATUS_LLM_FAILED, error_message="无ASR数据")
            # Ensure the button text is reset if it was "增强中..."
            entry = self.combined_file_status_panel.file_entries.get(file_path)
            if entry: entry["llm_enhance_button"].configure(text="LLM增强")
            return

        original_subs = self.generated_subtitle_data_map[file_path]
        full_original_text = "\n".join([item.text for item in original_subs if item.text])
        if not full_original_text.strip():
            self.logger.warning(f"无法为 {file_path} 执行LLM增强: 原始字幕文本为空。")
            self.combined_file_status_panel.update_file_status(file_path, CombinedFileStatusPanel.STATUS_LLM_FAILED, error_message="ASR文本为空")
            entry = self.combined_file_status_panel.file_entries.get(file_path)
            if entry: entry["llm_enhance_button"].configure(text="LLM增强")
            return

        ui_settings = self.settings_panel.get_settings()
        api_key = ui_settings.get("llm_api_key")
        base_url = ui_settings.get("llm_base_url")
        model_name = ui_settings.get("llm_model_name")
        user_defined_system_prompt = ui_settings.get("llm_system_prompt", "") # Allow empty
        llm_script_context = ui_settings.get("llm_script_context", "") # Get script context
        temperature = 0.7 # TODO: Make this configurable later if needed

        # Construct final system prompt content
        final_system_prompt_content = user_defined_system_prompt.strip() if user_defined_system_prompt.strip() else "You are a helpful assistant."
        # Append script context if available
        if llm_script_context and llm_script_context.strip(): # Corrected '&&' to 'and'
            final_system_prompt_content += f"\n\n--- 参考剧本/上下文 ---\n{llm_script_context}"

        if not api_key or not base_url or not model_name:
            self.logger.error(f"无法为 {file_path} 执行LLM增强: LLM配置不完整 (API Key, Base URL, 或 Model Name 缺失)。")
            messagebox.showerror("LLM配置错误", "请在AI设置中配置完整的LLM API Key, Base URL, 和模型名称。")
            self.combined_file_status_panel.update_file_status(file_path, CombinedFileStatusPanel.STATUS_ASR_DONE) # Revert status to allow retry
            entry = self.combined_file_status_panel.file_entries.get(file_path)
            if entry: entry["llm_enhance_button"].configure(text="LLM增强") # Reset button text
            return
        
        # Ensure base_url doesn't end with / for constructing the endpoint
        cleaned_base_url = base_url.rstrip('/')
        target_url = f"{cleaned_base_url}/v1/chat/completions"

        # Prepare for curl command - JSON escaping is crucial for the -d part
        import json # Make sure json is imported

        # The following escaping is not needed as json.dumps on the payload_dict handles it.
        # escaped_system_prompt = json.dumps(final_system_prompt_content)[1:-1]
        # escaped_user_content = json.dumps(full_original_text)[1:-1]

        # Construct messages list
        messages = [
            {"role": "system", "content": final_system_prompt_content},
            {"role": "user", "content": full_original_text}
        ]
        
        # Construct the data payload string manually to ensure correct escaping for cmd.exe
        # This is tricky because cmd.exe handles quotes differently.
        # A robust way is to prepare the JSON string in Python, then escape THAT for cmd.
        
        payload_dict = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature
        }
        payload_json_str = json.dumps(payload_dict)
        
        # For Windows CMD, need to escape double quotes inside the JSON string for -d "..."
        # if the JSON itself contains double quotes. json.dumps will handle internal JSON string escaping.
        # The main challenge is passing this string literal correctly via cmd.exe.
        # A common way for curl on Windows with JSON:
        # curl ... -d "{ \"model\": \"gpt-3.5\", ... }"
        # So, we need to escape the double quotes within payload_json_str if it's wrapped by double quotes in cmd.
        # However, `execute_command` might handle this. Let's try simpler first.

        # Simplification: Assume execute_command handles parameters well, or test.
        # If using -d '...', then internal double quotes are fine. But cmd.exe prefers -d "...".
        # Let's try to prepare a command that is generally more robust.
        # One way is to write the payload to a temporary file and use curl -d @payload.json, but that's more steps.
        
        # Constructing the -d part carefully for cmd.exe:
        # The `payload_json_str` is already a valid JSON string.
        # When passing to `curl -d` on Windows, if `payload_json_str` contains `"` they must be escaped as `\"`.
        # And the whole thing wrapped in `"` for `curl -d "..."`.
        # So if payload_json_str is `{"key":"val"}`, cmd needs `curl -d "{\"key\":\"val\"}"`
        
        # Python's `json.dumps` produces: '{"model": "gpt-3.5-turbo", ...}'
        # We need to pass this to `curl -d`
        # `execute_command` takes a single string.

        curl_data_payload = payload_json_str.replace('"', '\\"') # Escape internal quotes for cmd

        # Note: The Authorization header Bearer token might itself have issues if it contains special cmd characters.
        # Assuming API keys are typically safe for this.
        
        # Using a list of arguments for clarity before joining, though execute_command takes a string.
        curl_command_parts = [
            "curl", "-s", "-X", "POST", target_url,
            "-H", f"\"Content-Type: application/json\"",
            "-H", f"\"Authorization: Bearer {api_key}\"",
            "-d", f"\"{curl_data_payload}\"" # Wrap the escaped JSON in quotes for -d
        ]
        curl_command_str = " ".join(curl_command_parts)
        
        self.logger.info(f"Constructed curl command for LLM enhancement: {curl_command_str[:150]}...") # Log only a part due to length
        # Log full command for debugging if needed, but be wary of API key in logs for production
        # self.logger.debug(f"Full curl command: {curl_command_str}")

        # Update UI for the specific file to show "LLM Enhancing..."
        entry = self.combined_file_status_panel.file_entries.get(file_path)
        if entry:
            entry["llm_enhance_button"].configure(text="增强中...", state="disabled")
            # Optionally update status label if desired
            # entry["status_label"].configure(text=CombinedFileStatusPanel.STATUS_PROCESSING_LLM, text_color="orange")

        # Store context for when the result comes back from AI agent
        if not hasattr(self, 'pending_llm_enhancements'):
            self.pending_llm_enhancements = {}
        self.pending_llm_enhancements[file_path] = {
            "original_subs": original_subs, # Storing original subs for context
            "curl_command": curl_command_str # Storing for reference if needed
        }
        
        # Log the command for the AI agent (Roo) to execute
        self.logger.info(f"ROO_EXECUTE_CURL_LLM:::FILEPATH='{file_path}':::COMMAND='{curl_command_str}'")
        self.app.status_label.configure(text=f"状态: {os.path.basename(file_path)} - 等待AI执行LLM增强命令...")

        # Cancel any existing timeout for this file path before setting a new one
        if file_path in self._llm_enhancement_after_ids:
            existing_after_id = self._llm_enhancement_after_ids.pop(file_path)
            try:
                self.after_cancel(existing_after_id)
                self.logger.debug(f"Cancelled previous LLM enhancement timeout for {file_path}, ID: {existing_after_id}")
            except Exception as e_cancel: # Tkinter can raise TclError if ID is invalid
                self.logger.warning(f"Error cancelling previous LLM enhancement timeout ID {existing_after_id} for {file_path}: {e_cancel}")
        
        after_id = self.after(self.llm_enhancement_timeout_ms,
                              lambda fp=file_path: self._handle_llm_enhancement_timeout(fp))
        self._llm_enhancement_after_ids[file_path] = after_id
        self.logger.info(f"LLM增强超时已为 {file_path} 设置 ({self.llm_enhancement_timeout_ms / 1000}s), ID: {after_id}")

        # Cancel any existing timeout for this file path before setting a new one
        if file_path in self._llm_enhancement_after_ids:
            existing_after_id = self._llm_enhancement_after_ids.pop(file_path)
            self.after_cancel(existing_after_id)
            self.logger.debug(f"Cancelled previous LLM enhancement timeout for {file_path}")

        after_id = self.after(self.llm_enhancement_timeout_ms,
                              lambda fp=file_path: self._handle_llm_enhancement_timeout(fp))
        self._llm_enhancement_after_ids[file_path] = after_id
        self.logger.info(f"LLM增强超时已为 {file_path} 设置 ({self.llm_enhancement_timeout_ms / 1000}s), ID: {after_id}")

    def process_llm_enhancement_result(self, file_path: str, stdout_str: str, stderr_str: str, exit_code: int):
        """
        Processes the result of the curl command executed for LLM enhancement.
        This method is intended to be called by the AI agent after it receives
        the result from the execute_command tool.
        """
        # Ensure json and pysrt are imported at the top of the file or ensure they are accessible here
        # import json # Already at top
        # import pysrt # Already at top
        self.logger.info(f"处理LLM增强结果 for {file_path}. Exit code: {exit_code}")
        
        context = None
        if hasattr(self, 'pending_llm_enhancements') and file_path in self.pending_llm_enhancements:
            context = self.pending_llm_enhancements.pop(file_path)
        
        if context is None:
            self.logger.error(f"LLM增强结果处理错误: 未找到 {file_path} 的待处理上下文。")
            self.app.after(0, lambda: self.combined_file_status_panel.update_file_status(file_path, CombinedFileStatusPanel.STATUS_LLM_FAILED, error_message="内部上下文错误"))
            return

        original_subs_data = context.get("original_subs")
        if original_subs_data is None:
             self.logger.error(f"LLM增强结果处理错误: {file_path} 的待处理上下文中缺少 original_subs。")
             self.app.after(0, lambda: self.combined_file_status_panel.update_file_status(file_path, CombinedFileStatusPanel.STATUS_LLM_FAILED, error_message="无原始字幕"))
             return
        
        try:
            if exit_code == 0:
                self.logger.debug(f"curl LLM增强 for {file_path} 成功. stdout (first 200): {stdout_str[:200]}...")
                response_data = json.loads(stdout_str)
                
                choices = response_data.get('choices')
                if choices and isinstance(choices, list) and len(choices) > 0:
                    first_choice = choices[0]
                    if isinstance(first_choice, dict) and first_choice.get('message') and \
                       isinstance(first_choice['message'], dict):
                        enhanced_text_raw = first_choice['message'].get('content')
                        if enhanced_text_raw is not None:
                            enhanced_full_text = enhanced_text_raw.strip()
                            if not enhanced_full_text:
                                self.logger.warning(f"LLM for {file_path} returned empty content.")
                                raise ValueError("LLM returned empty content")

                            # Strategy: Replace original subs with a single new sub containing all enhanced text.
                            # Timestamps from the very first and very last original segment.
                            new_subs = []
                            if original_subs_data:
                                first_item_start = original_subs_data[0].start
                                last_item_end = original_subs_data[-1].end
                                if first_item_start > last_item_end : # Safety for single item case
                                    last_item_end = first_item_start
                                
                                new_item = pysrt.SubRipItem(
                                    index=1,
                                    start=first_item_start,
                                    end=last_item_end,
                                    text=enhanced_full_text
                                )
                                new_subs.append(new_item)
                            else: # Should not happen if we checked before calling
                                new_subs.append(pysrt.SubRipItem(index=1, start=pysrt.SubRipTime(0), end=pysrt.SubRipTime(seconds=5), text=enhanced_full_text))

                            self.generated_subtitle_data_map[file_path] = new_subs
                            self.logger.info(f"Successfully updated subtitle data for {file_path} with LLM enhanced content.")
                            self.app.after(0, lambda: self.combined_file_status_panel.update_file_status(file_path, CombinedFileStatusPanel.STATUS_LLM_DONE))
                            self.app.after(0, lambda: self.app.status_label.configure(text=f"状态: {os.path.basename(file_path)} LLM增强完成。"))
                            
                            # If currently previewing this file, refresh the editor
                            if self.results_panel_handler.current_previewing_file == file_path:
                                self.app.after(0, lambda p=file_path: self.results_panel_handler.set_main_preview_content(p))
                            return
                        else: # content is None
                            raise ValueError("'content' field missing in LLM response message.")
                    else: # message field missing
                        raise ValueError("Invalid 'message' field in LLM response choice.")
                else: # choices array missing
                    raise ValueError("Invalid 'choices' array in LLM API response.")
            else: # exit_code != 0
                self.logger.error(f"curl LLM增强 for {file_path} 失败. Exit code: {exit_code}")
                self.logger.error(f"stderr: {stderr_str}")
                self.logger.error(f"stdout: {stdout_str}") # Also log stdout in case of error message there
                error_detail_for_ui = stderr_str[:30] if stderr_str else f"Curl exit: {exit_code}"
                raise Exception(error_detail_for_ui)

        except Exception as e:
            self.logger.error(f"处理LLM增强结果时发生错误 for {file_path}: {e}", exc_info=True)
            error_msg_for_ui = str(e)[:30]
            self.app.after(0, lambda: self.combined_file_status_panel.update_file_status(file_path, CombinedFileStatusPanel.STATUS_LLM_FAILED, error_message=error_msg_for_ui))
            self.app.after(0, lambda: self.app.status_label.configure(text=f"状态: {os.path.basename(file_path)} LLM增强失败。"))
        finally:
             # Ensure button text is reset from "增强中..."
             entry = self.combined_file_status_panel.file_entries.get(file_path)
             if entry:
                  self.app.after(0, lambda btn=entry["llm_enhance_button"]: btn.configure(text="LLM增强"))

    def request_llm_test_connection(self):
        """
   Prepares a curl command to test the LLM connection.
   Called by SettingsPanel. The command is logged for the AI agent to execute.
   """
        self.logger.info("LLM连接测试请求 (UI触发)")
        # Ensure SettingsPanel is available. It should be as it calls this.
        if not hasattr(self, 'settings_panel') or self.settings_panel is None:
            self.logger.error("SettingsPanel 未初始化，无法获取LLM测试配置。")
            messagebox.showerror("内部错误", "无法执行LLM测试：UI组件未就绪。")
            return

        ui_settings = self.settings_panel.get_settings()
        api_key = ui_settings.get("llm_api_key")
        base_url = ui_settings.get("llm_base_url")
        model_name = ui_settings.get("llm_model_name")

        if not api_key or not base_url or not model_name:
            self.logger.error("无法测试LLM连接: 配置不完整。")
            messagebox.showerror("LLM配置错误", "请在AI设置中提供API Key, Base URL, 和模型名称以进行测试。")
            return

        cleaned_base_url = base_url.rstrip('/')
        target_url = f"{cleaned_base_url}/v1/chat/completions"

        test_payload_dict = {
            "model": model_name,
            "messages": [{"role": "user", "content": "Hello."}],
            "max_tokens": 5, # Keep response very short
            "temperature": 0.7
        }
        # json import should be at the top of the file
        payload_json_str = json.dumps(test_payload_dict)
        curl_data_payload_escaped_for_cmd = payload_json_str.replace('"', '\\"')
        data_payload_for_shell = f'"{curl_data_payload_escaped_for_cmd}"'
        
        header_content_type = '"Content-Type: application/json"'
        header_auth = f'"Authorization: Bearer {api_key}"'

        curl_command_str = (
            f'curl -X POST "{target_url}" '
            f'-H {header_content_type} -H {header_auth} '
            f'-d {data_payload_for_shell} '
            f'--connect-timeout 10 --max-time 20 -S' # -S to show server errors
        )
        
        self.logger.info("准备好的LLM连接测试curl命令。")
        self.logger.debug(f"LLM测试Curl命令 (first 150): {curl_command_str[:150]}...")

        # Simple flag for test pending, as only one test should run at a time.
        self.llm_test_pending = True

        self.app.status_label.configure(text="状态: 正在准备LLM连接测试...")
        # For the AI agent (Roo) to execute:
        self.logger.info(f"ROO_EXECUTE_CURL_LLM_TEST:::COMMAND='{curl_command_str}'")

        # Cancel any existing test timeout before setting a new one
        if self.llm_test_pending_id:
            try:
                self.after_cancel(self.llm_test_pending_id)
                self.logger.debug(f"Cancelled previous LLM test timeout, ID: {self.llm_test_pending_id}")
            except Exception as e_cancel:
                 self.logger.warning(f"Error cancelling previous LLM test timeout ID {self.llm_test_pending_id}: {e_cancel}")
            self.llm_test_pending_id = None
        
        self.llm_test_pending = True # Set flag that a test is now officially pending AI response
        self.llm_test_pending_id = self.after(self.llm_test_timeout_ms, self._handle_llm_test_timeout)
        self.logger.info(f"LLM连接测试超时已设置 ({self.llm_test_timeout_ms / 1000}s), ID: {self.llm_test_pending_id}")

    def process_llm_test_connection_result(self, stdout_str: str, stderr_str: str, exit_code: int):
        """
        Processes the result of the LLM test curl command.
        Called by the AI agent after command execution.
        """
        self.logger.info(f"处理LLM连接测试结果. Exit Code: {exit_code}")
        self.llm_test_pending = False # Reset flag
        
        success = False
        message_to_show = ""

        if exit_code == 0:
            try:
                # json import should be at the top
                response_data = json.loads(stdout_str)
                if response_data and (response_data.get('choices') or response_data.get('id') or response_data.get('object') == 'chat.completion'):
                    success = True
                    message_to_show = "LLM连接测试成功！服务可用。\n\n响应 (部分):\n" + stdout_str[:250]
                    self.logger.info(f"LLM连接测试成功. Response: {stdout_str[:250]}")
                else:
                    message_to_show = "LLM连接测试警告：服务返回了意外的JSON结构 (可能仍工作)。\n\n" + stdout_str[:250]
                    self.logger.warning(f"LLM连接测试收到意外JSON: {stdout_str}")
            except json.JSONDecodeError:
                message_to_show = "LLM连接测试失败：无法解析服务响应 (不是有效的JSON)。\n可能API URL不正确或服务未运行。\n\n响应内容 (部分):\n" + stdout_str[:250]
                self.logger.error(f"LLM连接测试JSON解析失败. stdout: {stdout_str}")
        else:
            message_to_show = f"LLM连接测试失败 (curl命令执行错误)。\n\nExit Code: {exit_code}\n"
            if stderr_str:
                message_to_show += f"错误信息 (部分):\n{stderr_str[:250]}"
                self.logger.error(f"LLM连接测试curl失败. Stderr: {stderr_str}")
            elif stdout_str:
                 message_to_show += f"输出 (部分):\n{stdout_str[:250]}"
                 self.logger.error(f"LLM连接测试curl失败. Stdout: {stdout_str}")
            else:
                message_to_show += "未获取到curl的错误输出。请检查Base URL是否正确，以及服务是否正在运行。"
        
        # Determine master for messagebox
        master_mb = self.app if hasattr(self, 'app') and self.app else self

        if success:
            messagebox.showinfo("LLM连接测试", message_to_show, master=master_mb)
        else:
            messagebox.showerror("LLM连接测试", message_to_show, master=master_mb)
        
        if hasattr(self, 'app') and hasattr(self.app, 'status_label'):
            self.app.status_label.configure(text=f"状态: LLM连接测试{'成功' if success else '失败'}。")

    def request_asr_for_single_file(self, file_path: str):
        """Handles the request to process ASR for a single specific file."""
        self.logger.info(f"单文件ASR处理请求: {file_path}")

        if self.top_controls_panel.is_processing: # Check if main processing is active
            messagebox.showwarning("处理中", "另一个处理任务正在进行中。请稍后再试。", master=self.app or self)
            self.logger.warning("单文件ASR请求被拒绝：已有处理任务在运行。")
            entry = self.combined_file_status_panel.file_entries.get(file_path)
            if entry: # Reset button visuals if they were changed by CombinedFileStatusPanel
                entry["generate_asr_button"].configure(state="normal", text="生成ASR")
            return # Exit if another process is running

        # If not processing, continue with single file ASR
        # Set UI to a processing state for this single file action
        self.top_controls_panel.set_ui_for_processing(is_processing=True) # Blocks main start
        self.app.status_label.configure(text=f"状态: 正在准备处理文件: {os.path.basename(file_path)}")
        if hasattr(self.results_panel_handler, 'set_main_preview_content'):
            self.results_panel_handler.set_main_preview_content(None) # Clear editor if any preview was active
        
        self.update_idletasks() # Ensure UI updates
        self.logger.info(f"准备开始单文件处理: {file_path}")

        single_processing_thread = threading.Thread(
            target=self._run_single_file_processing_in_thread,
            args=(file_path,),
            daemon=True
        )
        single_processing_thread.start()

    def _handle_llm_enhancement_timeout(self, file_path: str):
        """Handles LLM enhancement timeout for a specific file."""
        if file_path in self._llm_enhancement_after_ids: # Check if it wasn't cancelled by a result
            self._llm_enhancement_after_ids.pop(file_path) # Remove to prevent further cancellation attempts
            
            if file_path in self.pending_llm_enhancements:
                self.pending_llm_enhancements.pop(file_path) # Clear pending context
                self.logger.warning(f"LLM增强超时 for {file_path}。AI代理未在规定时间内返回结果。")
                self.app.status_label.configure(text=f"状态: {os.path.basename(file_path)} - LLM增强请求超时。")
                
                # Update UI for the specific file to show timeout error
                self.combined_file_status_panel.update_file_status(
                    file_path,
                    CombinedFileStatusPanel.STATUS_LLM_FAILED,
                    error_message="AI响应超时"
                )
                # Ensure the button is re-enabled and text is reset
                entry = self.combined_file_status_panel.file_entries.get(file_path)
                if entry:
                    entry["llm_enhance_button"].configure(text="LLM增强", state="normal") # Re-enable
            else:
                self.logger.info(f"LLM增强超时回调 for {file_path}, 但该文件已不在待处理列表中。可能已被正常处理。")
        else:
            self.logger.debug(f"LLM增强超时回调 for {file_path}, 但 after_id 已被移除。可能已被取消。")

    def _handle_llm_test_timeout(self):
        """Handles LLM connection test timeout."""
        if self.llm_test_pending_id: # Clear the ID first
            self.llm_test_pending_id = None
            
            if self.llm_test_pending: # Check if the test was actually still considered pending
                self.llm_test_pending = False
                self.logger.warning("LLM连接测试超时。AI代理未在规定时间内返回结果。")
                self.app.status_label.configure(text="状态: LLM连接测试请求超时。")
                messagebox.showwarning("LLM测试超时", "LLM连接测试请求超时，AI代理未及时响应。", master=self.app or self)
                
                # Re-enable test button in SettingsPanel if applicable
                if hasattr(self.settings_panel, 'llm_test_connection_button'):
                    self.settings_panel.llm_test_connection_button.configure(state="normal")
            else:
                self.logger.info("LLM测试超时回调，但测试已不处于待处理状态。可能已被正常处理。")
        else:
            self.logger.debug("LLM测试超时回调，但 after_id 已被移除。可能已被取消。")

    def _run_single_file_processing_in_thread(self, file_path_to_process: str):
        """Runs the ASR processing workflow for a single specified file."""
        # Imports needed in thread if not already at module level and certain of access
        # import os # Already at module level
        # import pysrt # Already at module level
        
        # Make sure json is imported for any LLM related data structures, even if LLM is off for this run
        # import json # Already at module level
        
        # Ensure WorkflowManager's parameters are up-to-date from current config/UI settings
        # This mirrors part of the logic in _run_processing_in_thread but for a single context.
        try:
            ui_settings = self.settings_panel.get_settings()
            current_lang = ui_settings.get("language", self.config.get("language", "en"))
            current_dict_path = ui_settings.get(f"custom_dictionary_path_{current_lang}",
                                                self.config.get(f"custom_dictionary_path_{current_lang}", ""))
            
            # Update WorkflowManager's internal state for this run if necessary
            # Note: set_language also updates normalizer and punctuator if they exist
            self.workflow_manager.set_language(current_lang)
            self.workflow_manager.set_custom_dictionary(current_dict_path, current_lang)
            self.workflow_manager.update_processing_parameters(
                min_duration_sec=float(self.config.get("min_duration_sec", 1.0)),
                min_gap_sec=float(self.config.get("min_gap_sec", 0.1))
            )
            # Update LLM enhancer within workflow manager if it's to be used, even if llm_enabled=False for this run
            # This ensures its internal state (like system prompt) is current if user later clicks LLM enhance.
            # However, the main LLM re-init is in process_audio_to_subtitle
            # --- 用户反馈：此按钮专用于ASR，不应更新LLM配置 ---
            # if hasattr(self.workflow_manager, 'llm_enhancer') and self.workflow_manager.llm_enhancer:
            #      self.workflow_manager.llm_enhancer.update_config(
            #         api_key=ui_settings.get("llm_api_key"),
            #         base_url=ui_settings.get("llm_base_url"),
            #         model_name=ui_settings.get("llm_model_name"),
            #         system_prompt=ui_settings.get("llm_system_prompt", ""),
            #         script_context=ui_settings.get("llm_script_context", ""), # Pass script context for internal state
            #         language=current_lang # Corrected 'language_code' to 'language'
            #      )


            base_filename = os.path.basename(file_path_to_process)
            status_prefix = f"处理中: {base_filename}"
            self.logger.info(f"{status_prefix} ASR: {ui_settings['asr_model']}. LLM手动触发.")
            
            self.app.after(0, lambda sp=status_prefix: self.app.status_label.configure(text=f"状态: {sp}"))
            # CombinedFileStatusPanel updates its own item to "ASR处理中..."

            # Perform ASR (LLM enhancement is explicitly off for this direct ASR step)
            preview_text, structured_subtitle_data = self.workflow_manager.process_audio_to_subtitle(
                audio_video_path=file_path_to_process,
                asr_model=ui_settings["asr_model"],
                device=ui_settings["device"],
                llm_enabled=False, # LLM is manually triggered later
                llm_params=None,   # Not needed as llm_enabled is False
                output_format="srt", # For preview, not final export
                current_custom_dict_path=current_dict_path, # Already set in WM via set_custom_dictionary
                processing_language=current_lang # Already set in WM via set_language
                # min_duration_sec and min_gap_sec are now part of WM's internal state
            )
            
            self.generated_subtitle_data_map[file_path_to_process] = structured_subtitle_data
            self.app.after(0, lambda p=file_path_to_process, s_data=structured_subtitle_data:
                           self.handle_processing_success_for_combined_panel(p, s_data))
            
            self.logger.info(f"文件 {base_filename} 单独ASR处理成功。")
            # Status in CombinedFileStatusPanel will be updated by handle_processing_success_for_combined_panel
            # Main status bar update
            self.app.after(0, lambda bf=base_filename: self.app.status_label.configure(text=f"状态: {bf} ASR完成。"))
            
            # Optionally, auto-preview the processed file
            if hasattr(self.results_panel_handler, 'set_main_preview_content'):
                self.app.after(0, lambda path=file_path_to_process: self.results_panel_handler.set_main_preview_content(path))
            
            self.app.after(0, self.update_export_all_button_state)

        except Exception as e_single:
            base_filename = os.path.basename(file_path_to_process) # Define here for except block
            self.logger.error(f"处理单文件 {base_filename} 时发生错误: {e_single}", exc_info=True)
            # Update CombinedFileStatusPanel with error for the specific file
            self.app.after(0, lambda p=file_path_to_process, err=str(e_single):
                           self.combined_file_status_panel.update_file_status(p, CombinedFileStatusPanel.STATUS_ERROR, error_message=err, processing_done=True)) # processing_done=True to enable retry
            self.app.after(0, lambda bf=base_filename: self.app.status_label.configure(text=f"状态: {bf} ASR处理失败。"))
        finally:
            # Reset the main processing UI lock
            self.app.after(0, lambda: self.top_controls_panel.set_ui_for_processing(is_processing=False))
            # The individual button's state (e.g., "生成ASR" or disabled) is handled by update_file_status
            # called within handle_processing_success_for_combined_panel or the except block above.

            # Update general status bar if not specifically set by success/failure message for this file
            current_status_main = self.app.status_label.cget("text")
            expected_success_msg = f"状态: {os.path.basename(file_path_to_process)} ASR完成。"
            expected_fail_msg = f"状态: {os.path.basename(file_path_to_process)} ASR处理失败。"
            if current_status_main not in [expected_success_msg, expected_fail_msg]:
                 self.app.after(0, lambda: self.app.status_label.configure(text=f"状态: 操作结束。"))


# For testing MainWindow independently
if __name__ == '__main__': # Corrected indent to 0 spaces
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