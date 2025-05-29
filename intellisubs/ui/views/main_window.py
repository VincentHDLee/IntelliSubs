# Main Window for IntelliSubs Application
import customtkinter as ctk
import json
from tkinter import filedialog, messagebox
import os
import threading # For running processing in a separate thread
import logging # For the test __main__ logger
import asyncio # For _async_run_llm_test
import pysrt # For SubRipItem and SubRipTime objects

# Import component panels
from .main_window_components.top_controls_panel import TopControlsPanel
from .main_window_components.settings_panel import SettingsPanel
from .main_window_components.results_panel import ResultsPanel
from .main_window_components.combined_file_status_panel import CombinedFileStatusPanel

# For testing standalone (if this file is run directly)
from ...utils.config_manager import ConfigManager
from ...utils.logger_setup import setup_logging
from ...core.workflow_manager import WorkflowManager
from ...core.text_processing.llm_enhancer import LLMEnhancer # Added import


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
                f"custom_dictionary_path_{ui_settings['language']}": ui_settings.get(f"custom_dictionary_path_{ui_settings['language']}", ""),
                "llm_enabled": ui_settings["llm_enabled"],
                "llm_api_key": ui_settings["llm_api_key"],
                "llm_base_url": ui_settings.get("llm_base_url") if ui_settings.get("llm_base_url") else None, # from get_settings
                "llm_model_name": ui_settings["llm_model_name"],
                "llm_system_prompt": ui_settings.get("llm_system_prompt", ""),
                "llm_script_context": ui_settings.get("llm_script_context", "") # Ensure script context is part of config updates
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
                            "base_url": self.config.get("llm_base_url"), # Use from self.config (now updated)
                            "model_name": ui_settings["llm_model_name"],
                            "system_prompt": ui_settings.get("llm_system_prompt", ""),
                            "script_context": self.config.get("llm_script_context", "") # Use from self.config (now updated)
                        }

                    preview_text, structured_subtitle_data = self.workflow_manager.process_audio_to_subtitle(
                        audio_video_path=file_path,
                        asr_model=ui_settings["asr_model"],
                        device=ui_settings["device"],
                        llm_enabled=ui_settings["llm_enabled"],
                        llm_params=llm_params, # llm_params now includes script_context from self.config
                        output_format="srt",
                        current_custom_dict_path=current_dict_path,
                        processing_language=ui_settings["language"],
                        min_duration_sec=self.config.get("min_duration_sec", 1.0),
                        min_gap_sec=self.config.get("min_gap_sec", 0.1),
                        # llm_script_context can be removed if WorkflowManager reliably uses it from llm_params
                        llm_script_context=self.config.get("llm_script_context", "") 
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
                        self.app.after(0, lambda path=first_successful_path: self.results_panel_handler.set_main_preview_content(path))
                    elif error_count == len(self.selected_file_paths): # All failed
                         self.app.after(0, lambda: self.results_panel_handler.set_main_preview_content(None))
                    else: # Some processed, some failed, but none of the first ones were successful for preview
                        self.app.after(0, lambda: self.results_panel_handler.set_main_preview_content(None))

            elif error_count > 0 : # No successes, only errors
                self.app.after(0, lambda: self.results_panel_handler.set_main_preview_content(None))
            else: # No files processed
                self.app.after(0, lambda: self.results_panel_handler.set_main_preview_content(None))

            self.app.after(0, self.update_export_all_button_state)

        except Exception as e_batch:
            self.logger.exception(f"批量处理时发生意外错误: {e_batch}")
            self.app.after(0, lambda eb=e_batch: messagebox.showerror("批量处理错误", f"批量处理时发生意外错误: {eb}"))
            self.app.after(0, lambda: self.app.status_label.configure(text="状态: 批量处理失败"))
            self.app.after(0, lambda: self.results_panel_handler.set_main_preview_content(None)) # Clear editor
        finally:
            self.app.after(0, lambda: self.top_controls_panel.set_ui_for_processing(is_processing=False))
            self.app.after(0, self.top_controls_panel.update_start_button_state_based_on_files)
            
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

        if hasattr(self.top_controls_panel, 'update_file_path_display'):
            self.top_controls_panel.update_file_path_display(num_files=len(self.selected_file_paths))
        
        if self.results_panel_handler.current_previewing_file == file_path_removed:
            self.results_panel_handler.set_main_preview_content(None)
            self.logger.info(f"Cleared preview as removed file {file_path_removed} was being previewed.")

        self.update_export_all_button_state()
        self.top_controls_panel.update_start_button_state_based_on_files() # Update start button too

    # Duplicated method definition was removed in previous step.
    # def handle_file_removed_from_panel(self, file_path_removed: str):
        # ...

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
        
        base_url_from_ui = ui_settings.get("llm_base_url", "") 
        final_config_base_url = base_url_from_ui if base_url_from_ui else None 
        update_if_changed("llm_base_url", final_config_base_url)
        update_if_changed("llm_model_name", ui_settings["llm_model_name"])
        update_if_changed("llm_system_prompt", ui_settings.get("llm_system_prompt", ""))
        update_if_changed("llm_script_context", ui_settings.get("llm_script_context", "")) # Save script_context
        
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
        """Handles the request to LLM enhance a specific file."""
        self.logger.info(f"LLM增强请求: {file_path}")

        if not file_path in self.generated_subtitle_data_map or not self.generated_subtitle_data_map[file_path]:
            self.logger.error(f"无法为 {file_path} 执行LLM增强: 未找到原始ASR字幕数据。")
            self.combined_file_status_panel.update_file_status(file_path, CombinedFileStatusPanel.STATUS_LLM_FAILED, error_message="无ASR数据")
            entry = self.combined_file_status_panel.file_entries.get(file_path)
            if entry and entry.get("llm_enhance_button"): entry["llm_enhance_button"].configure(text="LLM增强")
            return

        original_subs_data_pysrt = self.generated_subtitle_data_map[file_path]

        if not isinstance(original_subs_data_pysrt, list) or not all(isinstance(s, pysrt.SubRipItem) for s in original_subs_data_pysrt):
            self.logger.error(f"LLM增强 {file_path} 失败: 原始字幕数据格式不正确 (期望 list of SubRipItem)。实际类型: {type(original_subs_data_pysrt)}，首元素类型: {type(original_subs_data_pysrt[0]) if original_subs_data_pysrt else 'N/A'}")
            self.combined_file_status_panel.update_file_status(file_path, CombinedFileStatusPanel.STATUS_LLM_FAILED, error_message="ASR数据格式错误(pysrt)")
            entry = self.combined_file_status_panel.file_entries.get(file_path)
            if entry and entry.get("llm_enhance_button"): entry["llm_enhance_button"].configure(text="LLM增强")
            return
        
        # Convert list[SubRipItem] to list[dict] for LLMEnhancer
        segments_for_enhancer = []
        for idx, item in enumerate(original_subs_data_pysrt):
            segments_for_enhancer.append({
                "id": str(item.index) if item.index else str(idx), # Ensure ID is a string, use list index as fallback
                "start": item.start.ordinal / 1000.0,
                "end": item.end.ordinal / 1000.0,
                "text": item.text
            })
        
        if not segments_for_enhancer:
            self.logger.warning(f"无法为 {file_path} 执行LLM增强: 转换后无有效片段。")
            self.combined_file_status_panel.update_file_status(file_path, CombinedFileStatusPanel.STATUS_LLM_FAILED, error_message="无ASR片段")
            entry = self.combined_file_status_panel.file_entries.get(file_path)
            if entry and entry.get("llm_enhance_button"): entry["llm_enhance_button"].configure(text="LLM增强")
            return

        # Check if all text segments are empty after conversion.
        if not any(seg.get("text", "").strip() for seg in segments_for_enhancer):
            self.logger.warning(f"无法为 {file_path} 执行LLM增强: 原始字幕文本为空。")
            self.combined_file_status_panel.update_file_status(file_path, CombinedFileStatusPanel.STATUS_LLM_FAILED, error_message="ASR文本为空")
            entry = self.combined_file_status_panel.file_entries.get(file_path)
            if entry and entry.get("llm_enhance_button"): entry["llm_enhance_button"].configure(text="LLM增强")
            return

        ui_settings = self.settings_panel.get_settings()
        api_key = ui_settings.get("llm_api_key")
        base_url = ui_settings.get("llm_base_url") # Stripped by get_settings, or ""
        model_name = ui_settings.get("llm_model_name")
        user_defined_system_prompt = ui_settings.get("llm_system_prompt", "")
        llm_script_context = ui_settings.get("llm_script_context", "")

        if not api_key:
            self.logger.error("LLM增强失败: API Key 未配置。")
            messagebox.showerror("LLM 错误", "请在设置中配置LLM API Key。")
            self.combined_file_status_panel.update_file_status(file_path, CombinedFileStatusPanel.STATUS_LLM_FAILED, error_message="API Key未配置")
            entry = self.combined_file_status_panel.file_entries.get(file_path)
            if entry and entry.get("llm_enhance_button"): entry["llm_enhance_button"].configure(text="LLM增强")
            return

        if not base_url: # Base URL (domain) is required
            self.logger.error("LLM增强失败: Base URL 未配置。")
            messagebox.showerror("LLM 错误", "请在设置中配置LLM Base URL (域名)。")
            self.combined_file_status_panel.update_file_status(file_path, CombinedFileStatusPanel.STATUS_LLM_FAILED, error_message="Base URL未配置")
            entry = self.combined_file_status_panel.file_entries.get(file_path)
            if entry and entry.get("llm_enhance_button"): entry["llm_enhance_button"].configure(text="LLM增强")
            return

        self.combined_file_status_panel.update_file_status(file_path, CombinedFileStatusPanel.STATUS_PROCESSING_LLM)
        self.app.status_label.configure(text=f"状态: 正在为 {os.path.basename(file_path)} 执行LLM增强...")

        # Cancel any previous timeout for this file
        existing_after_id = self._llm_enhancement_after_ids.pop(file_path, None)
        if existing_after_id:
            self.after_cancel(existing_after_id)

        # Set new timeout
        current_after_id = self.after(self.llm_enhancement_timeout_ms, 
                                     lambda p=file_path: self._handle_llm_enhancement_timeout(p))
        self._llm_enhancement_after_ids[file_path] = current_after_id

        # Prepare llm_params for WorkflowManager
        llm_params = {
            "api_key": api_key,
            "base_url": base_url,
            "model_name": model_name,
            "system_prompt": user_defined_system_prompt,
            "script_context": llm_script_context,
            "language": ui_settings.get("language", "ja") # Pass language for LLMEnhancer prompts
        }

        # Start LLM enhancement in a new thread
        threading.Thread(
            target=self._run_llm_enhancement_in_thread,
            args=(file_path, segments_for_enhancer, llm_params), # Pass converted segments
            daemon=True
        ).start()

    def _run_llm_enhancement_in_thread(self, file_path: str, segments_to_enhance: list, llm_params: dict):
        """
        Worker function to run async LLM enhancement.
        """
        self.logger.info(f"LLM增强线程启动: {file_path}, {len(segments_to_enhance)} segments, params: {llm_params.get('model_name')}")
        enhanced_segments = None
        error_msg = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Create a temporary enhancer for this call
            temp_enhancer = LLMEnhancer(
                api_key=llm_params["api_key"],
                model_name=llm_params["model_name"],
                base_url=llm_params["base_url"],
                language=llm_params.get("language", self.config.get("language", "ja")),
                logger=self.logger,
                script_context=llm_params.get("script_context"),
                user_override_system_prompt=llm_params.get("system_prompt"), # Corrected parameter name
                config_prompts=self.config.get("llm_prompts") # Add default prompts from global config
            )
            enhanced_segments = loop.run_until_complete(
                temp_enhancer.async_enhance_text_segments(segments_to_enhance)
            )
        except Exception as e:
            self.logger.error(f"LLM增强线程内发生错误 {file_path}: {e}", exc_info=True)
            error_msg = str(e)
        finally:
            if 'loop' in locals() and not loop.is_closed():
                loop.close()
            
            # Schedule UI update on the main thread
            # Check if the timeout for this file has already occurred
            if file_path in self._llm_enhancement_after_ids: # If still pending (not timed out)
                self.after_cancel(self._llm_enhancement_after_ids.pop(file_path)) # Cancel timeout
                self.after(0, self.process_llm_enhancement_result, file_path, enhanced_segments, error_msg)
            else: # Timeout already handled it
                self.logger.info(f"LLM增强结果 for {file_path} arrived after timeout was handled. Ignoring.")


    def process_llm_enhancement_result(self, file_path: str, enhanced_segments: list | None, error_message: str | None):
        """
        Processes the result of LLM enhancement and updates UI. Must be called from main thread.
        """
        base_filename = os.path.basename(file_path)
        self.logger.info(f"处理LLM增强结果 for {base_filename}. Error: {error_message is not None}")

        if error_message:
            self.logger.error(f"LLM增强失败 for {base_filename}: {error_message}")
            self.combined_file_status_panel.update_file_status(file_path, CombinedFileStatusPanel.STATUS_LLM_FAILED, error_message=str(error_message)[:100])
            self.app.status_label.configure(text=f"状态: {base_filename} LLM增强失败。")
            # Ensure button text is reset
            entry = self.combined_file_status_panel.file_entries.get(file_path)
            if entry and entry.get("llm_enhance_button"):
                entry["llm_enhance_button"].configure(text="LLM增强")
            return

        if enhanced_segments is None: # Should not happen if no error, but as a safeguard
            self.logger.error(f"LLM增强 for {base_filename} 返回 None 但没有错误信息。")
            self.combined_file_status_panel.update_file_status(file_path, CombinedFileStatusPanel.STATUS_LLM_FAILED, error_message="增强返回空")
            entry = self.combined_file_status_panel.file_entries.get(file_path)
            if entry and entry.get("llm_enhance_button"):
                entry["llm_enhance_button"].configure(text="LLM增强")
            return

        # Success
        self.logger.info(f"LLM增强成功 for {base_filename}. {len(enhanced_segments)} dict segments processed.")
        
        # Convert list[dict] from LLMEnhancer back to list[pysrt.SubRipItem] for storage
        enhanced_subrip_items = []
        for idx, seg_dict in enumerate(enhanced_segments):
            try:
                start_time_s = float(seg_dict.get('start', 0.0))
                end_time_s = float(seg_dict.get('end', 0.0))
                text_content = str(seg_dict.get('text', ''))
                # Use original index/id if available and it makes sense, otherwise use list index.
                # pysrt.SubRipItem index is 1-based. LLMEnhancer might pass back original 'id'.
                item_index = idx + 1
                try: # Try to use original index if it was passed as 'id' and is an int
                    original_id = seg_dict.get('id')
                    if original_id is not None:
                        item_index = int(original_id)
                except ValueError:
                    self.logger.warning(f"LLM result: Could not parse original_id '{seg_dict.get('id')}' as int for item {idx}, using list index.")

                start_obj = pysrt.SubRipTime(seconds=start_time_s)
                end_obj = pysrt.SubRipTime(seconds=end_time_s)
                if start_obj > end_obj: # Ensure start <= end
                    self.logger.warning(f"LLM result conversion: item {idx} has start > end ({start_obj} > {end_obj}). Clamping end to start.")
                    end_obj = start_obj
                
                enhanced_subrip_items.append(pysrt.SubRipItem(
                    index=item_index, start=start_obj, end=end_obj, text=text_content
                ))
            except Exception as e_conv:
                self.logger.error(f"Error converting LLM enhanced segment dict to SubRipItem for {base_filename}, segment {idx}: {seg_dict}, Error: {e_conv}", exc_info=True)
                continue # Skip this segment if conversion fails

        self.generated_subtitle_data_map[file_path] = enhanced_subrip_items # Update the stored data with SubRipItems
        self.logger.info(f"Stored {len(enhanced_subrip_items)} SubRipItems after LLM enhancement for {base_filename}.")
        self.combined_file_status_panel.update_file_status(file_path, CombinedFileStatusPanel.STATUS_LLM_DONE)
        self.app.status_label.configure(text=f"状态: {base_filename} LLM增强完成。")

        # If this file is currently being previewed, update the editor
        if self.results_panel_handler.current_previewing_file == file_path:
            self.results_panel_handler.set_main_preview_content(file_path) # This will re-fetch from map and update editor
        
        # Ensure export buttons state is updated as data changed
        self.update_export_all_button_state()


    def request_llm_test_connection(self):
        """Initiates a test of the LLM connection."""
        if not self.workflow_manager or not hasattr(self.workflow_manager, 'test_llm_connection_async'):
            self.logger.error("WorkflowManager or test_llm_connection_async method not available.")
            self.app.show_status_message("内部错误: 测试功能不可用。", error=True)
            if hasattr(self, 'settings_panel') and self.settings_panel: # Re-enable button if it exists
                 self.settings_panel.llm_test_connection_button.configure(state="normal", text="测试")
            return

        # Get current settings directly from UI vars for the test.
        api_key = self.settings_panel.llm_api_key_var.get().strip()
        base_url_for_test = self.settings_panel.llm_base_url_var.get().strip() # From UI, only stripped

        if not base_url_for_test:
            self.app.show_status_message("LLM测试: 请先配置 Base URL (域名)。", warning=True, duration_ms=4000)
            if hasattr(self, 'settings_panel') and self.settings_panel:
                self.settings_panel.llm_test_connection_button.configure(state="normal", text="测试")
            return
        
        test_config = {
            "llm_api_key": api_key,
            "llm_base_url": base_url_for_test, 
        }
        
        self.app.status_label.configure(text="状态: 正在测试LLM连接...")
        if self.settings_panel:
            self.settings_panel.llm_test_connection_button.configure(state="disabled", text="测试中...")

        threading.Thread(
            target=lambda: asyncio.run(self._async_run_llm_test(test_config)),
            daemon=True
        ).start()

    async def _async_run_llm_test(self, test_config_dict):
        """Helper to run the async test and process result."""
        if self.llm_test_pending_id: # Cancel previous timeout if any
            self.after_cancel(self.llm_test_pending_id)
            self.llm_test_pending_id = None
        
        self.llm_test_pending = True # Set flag
        self.llm_test_pending_id = self.after(self.llm_test_timeout_ms, self._handle_llm_test_timeout) # Set new timeout

        success, message = await self.workflow_manager.test_llm_connection_async(test_config_dict)
        
        if self.llm_test_pending: 
            self.llm_test_pending = False 
            if self.llm_test_pending_id: 
                self.after_cancel(self.llm_test_pending_id)
                self.llm_test_pending_id = None
        
        self.after(0, self.process_llm_test_connection_result, success, message) 


    def process_llm_test_connection_result(self, success: bool, message: str):
        """Processes the result of the LLM connection test and updates UI."""
        self.logger.info(f"LLM 连接测试结果: Success={success}, Message='{message}'")
        
        if hasattr(self, 'settings_panel') and self.settings_panel: 
            self.settings_panel.llm_test_connection_button.configure(state="normal", text="测试")

        if success:
            self.app.show_status_message(f"LLM连接测试: {message}", success=True, duration_ms=7000)
        else:
            self.app.show_status_message(f"LLM连接测试失败: {message}", error=True, duration_ms=10000)

        if success and hasattr(self, 'settings_panel') and self.settings_panel:
            self.logger.info("LLM connection test successful, attempting to refresh model list in UI.")
            self.settings_panel.fetch_llm_models_for_ui()


    def request_asr_for_single_file(self, file_path: str):
        """Initiates ASR processing for a single file via the context menu."""
        if not file_path:
            self.logger.warning("MainWindow: Request ASR for single file called with no file_path.")
            return

        self.logger.info(f"MainWindow: Requesting ASR for single file: {file_path}")
        
        self.combined_file_status_panel.update_file_status(file_path, "ASR处理中...")
        self.app.status_label.configure(text=f"状态: 正在为 {os.path.basename(file_path)} 执行ASR...")
        self.update_idletasks()

        processing_thread = threading.Thread(
            target=self._run_single_file_processing_in_thread,
            args=(file_path,),
            daemon=True
        )
        processing_thread.start()


    def _handle_llm_enhancement_timeout(self, file_path: str):
        if file_path in self._llm_enhancement_after_ids:
            self.logger.warning(f"LLM增强操作超时: {file_path}")
            self._llm_enhancement_after_ids.pop(file_path, None) 
            self.combined_file_status_panel.update_file_status(file_path, CombinedFileStatusPanel.STATUS_LLM_FAILED, error_message="操作超时")
            self.app.status_label.configure(text=f"状态: {os.path.basename(file_path)} LLM增强超时")
            entry = self.combined_file_status_panel.file_entries.get(file_path)
            if entry and entry.get("llm_enhance_button"):
                 entry["llm_enhance_button"].configure(text="LLM增强")


    def _handle_llm_test_timeout(self):
        if self.llm_test_pending: 
            self.logger.warning("LLM连接测试超时。")
            self.llm_test_pending = False 
            self.llm_test_pending_id = None 
            
            if hasattr(self, 'settings_panel') and self.settings_panel: 
                self.settings_panel.llm_test_connection_button.configure(state="normal", text="测试")
            self.app.show_status_message("LLM连接测试超时。", error=True, duration_ms=5000)


    def _run_single_file_processing_in_thread(self, file_path_to_process: str):
        """Runs the ASR processing workflow for a single specified file."""
        try:
            self.logger.info(f"单文件处理线程开始: {file_path_to_process}")
            ui_settings = self.settings_panel.get_settings() 
            
            # Temporarily update self.config with current UI settings for this specific run.
            # This ensures WorkflowManager uses the most up-to-date settings if it re-reads self.config
            # or if its internal components (like LLMEnhancer) are re-initialized based on self.config.
            # Back up original values to restore later.
            temp_config_override_keys = [
                "asr_model", "device", "language", f"custom_dictionary_path_{ui_settings['language']}",
                "llm_enabled", "llm_api_key", "llm_base_url", "llm_model_name", 
                "llm_system_prompt", "min_duration_sec", "min_gap_sec", "llm_script_context"
            ]
            original_config_backup = {key: self.config.get(key) for key in temp_config_override_keys}
            
            self.config["asr_model"] = ui_settings["asr_model"]
            self.config["device"] = ui_settings["device"]
            self.config["language"] = ui_settings["language"]
            self.config[f"custom_dictionary_path_{ui_settings['language']}"] = ui_settings.get(f"custom_dictionary_path_{ui_settings['language']}", "")
            self.config["llm_enabled"] = ui_settings["llm_enabled"]
            self.config["llm_api_key"] = ui_settings["llm_api_key"]
            self.config["llm_base_url"] = ui_settings.get("llm_base_url") if ui_settings.get("llm_base_url") else None
            self.config["llm_model_name"] = ui_settings["llm_model_name"]
            self.config["llm_system_prompt"] = ui_settings.get("llm_system_prompt", "")
            self.config["llm_script_context"] = ui_settings.get("llm_script_context", "") # Ensure script context is in temp config
            try: self.config["min_duration_sec"] = float(ui_settings.get("min_duration_sec", 1.0))
            except ValueError: self.config["min_duration_sec"] = 1.0
            try: self.config["min_gap_sec"] = float(ui_settings.get("min_gap_sec", 0.1))
            except ValueError: self.config["min_gap_sec"] = 0.1

            llm_params_for_single = None
            if ui_settings["llm_enabled"]:
                llm_params_for_single = {
                    "api_key": ui_settings["llm_api_key"],
                    "base_url": ui_settings.get("llm_base_url"), # From get_settings, already stripped or "" which becomes None
                    "model_name": ui_settings["llm_model_name"],
                    "system_prompt": ui_settings.get("llm_system_prompt", ""),
                    "script_context": ui_settings.get("llm_script_context","") # From get_settings
                }
            
            preview_text, structured_data = self.workflow_manager.process_audio_to_subtitle(
                audio_video_path=file_path_to_process,
                asr_model=self.config["asr_model"], # Use the (potentially temporarily updated) config
                device=self.config["device"],
                llm_enabled=self.config["llm_enabled"],
                llm_params=llm_params_for_single,
                output_format="srt",
                current_custom_dict_path=self.config.get(f"custom_dictionary_path_{self.config['language']}", ""),
                processing_language=self.config["language"],
                min_duration_sec=self.config["min_duration_sec"],
                min_gap_sec=self.config["min_gap_sec"],
                llm_script_context=self.config["llm_script_context"] # Use from temp config
            )
            
            self.config.update(original_config_backup) # Restore original config values

            self.generated_subtitle_data_map[file_path_to_process] = structured_data
            self.app.after(0, lambda p=file_path_to_process, s_data=structured_data: 
                           self.handle_processing_success_for_combined_panel(p, s_data))
            
            if len(self.selected_file_paths) == 1 and self.selected_file_paths[0] == file_path_to_process:
                self.app.after(0, lambda path=file_path_to_process: self.results_panel_handler.set_main_preview_content(path))
            elif self.results_panel_handler.current_previewing_file == file_path_to_process:
                self.app.after(0, lambda path=file_path_to_process: self.results_panel_handler.set_main_preview_content(path))


            self.logger.info(f"单文件ASR处理完成: {file_path_to_process}")
            self.app.after(0, lambda: self.app.status_label.configure(text=f"状态: {os.path.basename(file_path_to_process)} ASR完成。"))

        except Exception as e_single_file:
            self.logger.error(f"处理单文件 {file_path_to_process} 时发生错误: {e_single_file}", exc_info=True)
            self.app.after(0, lambda p=file_path_to_process, err=str(e_single_file): 
                           self.combined_file_status_panel.update_file_status(p, CombinedFileStatusPanel.STATUS_ERROR, error_message=err, processing_done=True))
            self.app.after(0, lambda: self.app.status_label.configure(text=f"状态: {os.path.basename(file_path_to_process)} ASR失败。"))
        finally:
            if 'original_config_backup' in locals(): # Ensure backup was created before trying to restore
                self.config.update(original_config_backup) # Restore in case of error too

            self.app.after(0, self.update_export_all_button_state)
            pass 

# --- Test Main ---
# Minimal stub for ConfigManager if needed by components during standalone testing
class MinimalConfigManager:
    def __init__(self, config_path="test_config.json"):
        self.config_path = config_path
        self.config = {}

    def load_config(self): return self.config
    def save_config(self, data): self.config = data

class MockApp(ctk.CTk): # Used for standalone testing
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("IntelliSubs - MainWindow Test")
        self.geometry("1000x700")

        # Setup logger for testing
        self.test_logger = setup_logging(level=logging.DEBUG)

        # Mock ConfigManager
        self.config_manager = MinimalConfigManager()
        self.config = self.config_manager.load_config()
        # Populate with some defaults if empty for testing
        if not self.config:
            self.config.update({
                "asr_model": "small", "device": "cpu", "language": "ja",
                "llm_enabled": False, "llm_api_key": "", "llm_base_url": "", "llm_model_name": "gpt-3.5-turbo",
                "llm_script_context": "", "llm_system_prompt": "",
                "min_duration_sec": 1.0, "min_gap_sec": 0.1,
                "output_dir": ""
            })

        # Mock WorkflowManager
        self.workflow_manager = WorkflowManager(config=self.config, logger=self.test_logger)
        
        # Status Label (mimicking app.py)
        self.status_label = ctk.CTkLabel(self, text="状态: 就绪", anchor="w")
        self.status_label.pack(side="bottom", fill="x", padx=10, pady=5)

        # MainWindow instance
        self.main_window_frame = MainWindow(self, config=self.config, workflow_manager=self.workflow_manager, logger=self.test_logger)
        self.main_window_frame.pack(expand=True, fill="both")

    def show_status_message(self, message, error=False, warning=False, success=False, duration_ms=None):
        """Mimics the App's status message display."""
        prefix = "状态: "
        if error: prefix = "错误: "
        elif warning: prefix = "警告: "
        elif success: prefix = "成功: "
        
        self.status_label.configure(text=f"{prefix}{message}")
        self.test_logger.info(f"Status Updated: {prefix}{message}")
        if duration_ms:
            self.after(duration_ms, lambda: self.status_label.configure(text="状态: 就绪"))


if __name__ == "__main__":
    app = MockApp()
    app.mainloop()