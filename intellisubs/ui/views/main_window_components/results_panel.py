import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import pysrt

class ResultsPanel(ctk.CTkFrame):
    def __init__(self, master, app_ref, logger, workflow_manager, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app_ref # Reference to the main IntelliSubsApp instance
        self.logger = logger
        self.workflow_manager = workflow_manager # For parsing and formatting subtitles

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=2) # Results list (scrollable frame)
        self.grid_rowconfigure(1, weight=1) # Preview textbox
        self.grid_rowconfigure(2, weight=0) # Export controls (fixed height)

        self.current_previewing_file = None
        self.generated_subtitle_data_map = {} # Will be populated by MainWindow
        self.preview_edited = False

        self._create_results_list_widgets()
        self._create_preview_widgets()
        self._create_export_controls()

    def _create_results_list_widgets(self):
        self.results_label = ctk.CTkLabel(self, text="处理结果:", font=ctk.CTkFont(weight="bold"))
        self.results_label.grid(row=0, column=0, padx=5, pady=(5,0), sticky="nw") # Changed sticky to nw

        self.result_list_scrollable_frame = ctk.CTkScrollableFrame(self, label_text="")
        self.result_list_scrollable_frame.grid(row=0, column=0, padx=5, pady=(30,5), sticky="nsew") # Added pady top for label
        self.result_list_scrollable_frame.grid_columnconfigure(0, weight=1)

    def _create_preview_widgets(self):
        self.preview_label = ctk.CTkLabel(self, text="字幕预览:", font=ctk.CTkFont(weight="bold"))
        self.preview_label.grid(row=1, column=0, padx=5, pady=(5,0), sticky="nw") # Changed sticky to nw
        
        self.subtitle_editor_scrollable_frame = ctk.CTkScrollableFrame(self, label_text="") # Placeholder for individual subtitle entries
        self.subtitle_editor_scrollable_frame.grid(row=1, column=0, padx=5, pady=(30,5), sticky="nsew")
        self.subtitle_editor_scrollable_frame.grid_columnconfigure(0, weight=1) # Ensure content within stretches
        # self.preview_textbox.bind("<KeyRelease>", self.on_preview_text_changed) # This binding will change

    def _create_export_controls(self):
        self.export_controls_frame = ctk.CTkFrame(self)
        self.export_controls_frame.grid(row=2, column=0, padx=5, pady=(5,5), sticky="ew")
        self.export_controls_frame.grid_columnconfigure(0, weight=0) # Format Menu
        self.export_controls_frame.grid_columnconfigure(1, weight=0) # Apply Changes
        self.export_controls_frame.grid_columnconfigure(2, weight=0) # Export Current
        self.export_controls_frame.grid_columnconfigure(3, weight=0) # Insert New (NEW)
        self.export_controls_frame.grid_columnconfigure(4, weight=1) # Export All (pushes others left)

        self.export_format_var = ctk.StringVar(value="SRT")
        self.export_options = ["SRT", "LRC", "ASS", "TXT"] # TODO: Get from config or core
        self.export_menu = ctk.CTkOptionMenu(self.export_controls_frame, variable=self.export_format_var, values=self.export_options)
        self.export_menu.grid(row=0, column=0, padx=(0,5), pady=5, sticky="w")

        self.apply_changes_button = ctk.CTkButton(self.export_controls_frame, text="应用更改", command=self.apply_preview_changes, state="disabled")
        self.apply_changes_button.grid(row=0, column=1, padx=5, pady=5, sticky="e")
        
        self.export_button = ctk.CTkButton(self.export_controls_frame, text="导出当前预览", command=self.export_current_preview, state="disabled")
        self.export_button.grid(row=0, column=2, padx=5, pady=5, sticky="e")

        self.insert_item_button = ctk.CTkButton(self.export_controls_frame, text="插入新行", command=self._insert_subtitle_item)
        self.insert_item_button.grid(row=0, column=3, padx=5, pady=5, sticky="e")

        self.export_all_button = ctk.CTkButton(self.export_controls_frame, text="导出所有成功", command=self.export_all_successful, state="disabled")
        self.export_all_button.grid(row=0, column=4, padx=(5,0), pady=5, sticky="e")

    def set_generated_data(self, data_map):
        self.generated_subtitle_data_map = data_map

    def clear_result_list(self):
        for widget in self.result_list_scrollable_frame.winfo_children():
            widget.destroy()
        # Clear existing items in subtitle_editor_scrollable_frame
        for widget in self.subtitle_editor_scrollable_frame.winfo_children():
            widget.destroy()
        # self.preview_textbox.configure(state="disabled") # No longer a single textbox
        self.apply_changes_button.configure(state="disabled")
        self.current_previewing_file = None
        self.export_button.configure(state="disabled")
        # self.export_all_button.configure(state="disabled") # MainWindow will manage this

    def add_result_entry(self, file_path, structured_data, preview_text_for_this_file, success, error_message=None):
        base_name = os.path.basename(file_path)
        entry_frame = ctk.CTkFrame(self.result_list_scrollable_frame)
        entry_frame.pack(fill="x", pady=2, padx=2)

        status_text = "完成" if success else f"错误: {error_message[:50]}..." if error_message else "错误"
        status_color = "green" if success else "red"
        
        info_label = ctk.CTkLabel(entry_frame, text=f"{base_name} - {status_text}", text_color=status_color if not success else None)
        info_label.pack(side="left", padx=5, pady=2, expand=True, fill="x")

        if success and structured_data:
            preview_button = ctk.CTkButton(
                entry_frame,
                text="预览",
                width=60,
                command=lambda p=file_path: self.set_main_preview_content(p)
            )
            preview_button.pack(side="right", padx=5, pady=2)
        
        # Auto-preview the first successful item or if it's the only one processed
        # This logic might be better handled by MainWindow after all results are added
        # if success and (not self.current_previewing_file or len(self.master.selected_file_paths_from_controls) == 1) : # master needs that attr
        #     self.set_main_preview_content(preview_text_for_this_file, file_path)


    def set_main_preview_content(self, file_path): # content param is obsolete
        self.logger.debug(f"Setting main preview content for: {file_path}")
        for widget in self.subtitle_editor_scrollable_frame.winfo_children():
            widget.destroy()

        self.current_previewing_file = file_path
        self.preview_edited = False
        self.apply_changes_button.configure(state="disabled")

        structured_data = self.generated_subtitle_data_map.get(file_path)
        self.subtitle_entry_widgets = [] # Reset for new file

        if structured_data:
            self.export_button.configure(state="normal")
            
            for index, item in enumerate(structured_data): # Assuming structured_data is a list of SubRipItem-like objects
                item_frame = ctk.CTkFrame(self.subtitle_editor_scrollable_frame)
                item_frame.pack(fill="x", pady=2, padx=(2,5))
                # Columns: 0:idx, 1:start, 2:end, 3:text (weight 1), 4:delete_btn
                item_frame.grid_columnconfigure(3, weight=1)

                idx_label = ctk.CTkLabel(item_frame, text=f"{index + 1}", width=30)
                idx_label.grid(row=0, column=0, padx=(2,3), pady=2, sticky="w")

                start_time_str = str(item.start)
                start_entry = ctk.CTkEntry(item_frame, width=100)
                start_entry.insert(0, start_time_str)
                start_entry.grid(row=0, column=1, padx=3, pady=2)
                start_entry.bind("<KeyRelease>", lambda event, i=index: self.on_individual_item_changed(event, i, "start"))

                end_time_str = str(item.end) # Assumes item.end is SubRipTime or similar
                end_entry = ctk.CTkEntry(item_frame, width=100)
                end_entry.insert(0, end_time_str)
                end_entry.grid(row=0, column=2, padx=3, pady=2)
                end_entry.bind("<KeyRelease>", lambda event, i=index: self.on_individual_item_changed(event, i, "end"))
                
                # Use a StringVar for the text_entry to handle potential newlines better if CTkEntry is kept simple
                # Or, if text is complex, a small CTkTextbox per line would be better but adds layout complexity.
                # For now, replacing newline for CTkEntry display.
                display_text = item.text.replace('\n', ' \\n ') if hasattr(item, 'text') and item.text else ""
                text_entry_var = ctk.StringVar(value=display_text)
                text_entry = ctk.CTkEntry(item_frame, textvariable=text_entry_var)
                text_entry.grid(row=0, column=3, padx=3, pady=2, sticky="ew")
                text_entry.bind("<KeyRelease>", lambda event, i=index: self.on_individual_item_changed(event, i, "text"))

                delete_button = ctk.CTkButton(item_frame, text="✕", width=25, command=lambda i=index: self._delete_subtitle_item(i))
                delete_button.grid(row=0, column=4, padx=(3,0), pady=2, sticky="e")

                self.subtitle_entry_widgets.append({
                    'frame': item_frame, # Keep for direct destruction if not full refresh
                    'start_entry': start_entry,
                    'end_entry': end_entry,
                    'text_entry_var': text_entry_var,
                    'text_entry': text_entry,
                    'item_index': index
                })
        else:
            self.export_button.configure(state="disabled")
            placeholder_text = f"文件 {os.path.basename(file_path)} 未生成有效字幕预览或无结构化数据。"
            if not file_path: # Handle case where file_path might be None initially
                 placeholder_text = "请先选择一个文件并成功生成字幕以进行预览和编辑。"
            
            placeholder_label = ctk.CTkLabel(self.subtitle_editor_scrollable_frame, text=placeholder_text)
            placeholder_label.pack(pady=10)

        self.logger.debug(f"Populated subtitle editor for {file_path} with {len(structured_data) if structured_data else 0} items.")

    def _delete_subtitle_item(self, item_list_index):
        self.logger.info(f"Attempting to delete subtitle item at list index: {item_list_index}")
        if not self.current_previewing_file:
            self.logger.warning("No file is currently being previewed. Cannot delete item.")
            return
        
        structured_data = self.generated_subtitle_data_map.get(self.current_previewing_file)
        if not structured_data or not isinstance(structured_data, list):
            self.logger.warning(f"No structured data or invalid data type for {self.current_previewing_file}. Cannot delete.")
            return

        if 0 <= item_list_index < len(structured_data):
            try:
                removed_item = structured_data.pop(item_list_index)
                self.logger.info(f"Removed item: {removed_item.text if hasattr(removed_item, 'text') else 'N/A'} from structured data.")
                
                # Mark as edited
                if not self.preview_edited:
                    self.preview_edited = True
                    self.apply_changes_button.configure(state="normal")
                
                # Refresh the entire editor view to re-index and update UI
                self.set_main_preview_content(self.current_previewing_file)
                messagebox.showinfo("删除成功", f"字幕行 {item_list_index + 1} 已删除。")

            except IndexError:
                self.logger.error(f"IndexError while trying to pop item at index {item_list_index} from structured_data (len: {len(structured_data)}).")
                messagebox.showerror("错误", "删除字幕行时发生索引错误。")
            except Exception as e:
                self.logger.error(f"Error deleting subtitle item at index {item_list_index}: {e}", exc_info=True)
                messagebox.showerror("错误", f"删除字幕行时发生未知错误: {e}")
        else:
            self.logger.warning(f"Invalid index {item_list_index} for deletion. Data length: {len(structured_data)}.")
            messagebox.showwarning("索引无效", "无法删除字幕行：索引超出范围。")

    def _insert_subtitle_item(self):
        self.logger.info("Attempting to insert a new subtitle item.")
        if not self.current_previewing_file:
            messagebox.showwarning("无预览", "请先预览一个文件才能插入新行。")
            self.logger.warning("Insert item: No file previewing.")
            return

        structured_data = self.generated_subtitle_data_map.get(self.current_previewing_file)
        if structured_data is None: # If key exists but data is None (should not happen if preview works)
            # Or if key doesn't exist, we want to start a new list
            structured_data = []
            self.generated_subtitle_data_map[self.current_previewing_file] = structured_data
            self.logger.info(f"Insert item: Initialized new structured_data list for {self.current_previewing_file}")
        
        # Determine start and end times for the new item
        new_start_time = pysrt.SubRipTime()
        new_end_time = pysrt.SubRipTime(seconds=1)

        if structured_data:
            last_item = structured_data[-1]
            # Ensure last_item.end is a SubRipTime object
            if isinstance(last_item.end, pysrt.SubRipTime):
                new_start_time = last_item.end + pysrt.SubRipTime(milliseconds=100)
                new_end_time = new_start_time + pysrt.SubRipTime(seconds=2) # Default 2 seconds duration
            else: # Fallback if last_item.end is not as expected
                self.logger.warning(f"Last item's end time is not a SubRipTime object. Type: {type(last_item.end)}. Using default times for new item.")
                # new_start_time and new_end_time will use their initial defaults
        else: # No existing items, new_start_time and new_end_time use their initial defaults
             self.logger.info("Insert item: Structured data is empty, using default times for the first item.")


        new_item_text = "[新字幕行]"
        new_pysrt_index = len(structured_data) + 1
        
        new_subtitle = pysrt.SubRipItem(
            index=new_pysrt_index,
            start=new_start_time,
            end=new_end_time,
            text=new_item_text
        )
        
        structured_data.append(new_subtitle)
        self.logger.info(f"New subtitle item created: Index {new_subtitle.index}, Start {new_subtitle.start}, End {new_subtitle.end}, Text '{new_subtitle.text}'")
        
        if not self.preview_edited:
            self.preview_edited = True
            self.apply_changes_button.configure(state="normal")
            self.logger.debug("Insert item: preview_edited set to True, apply_changes_button enabled.")
            
        self.set_main_preview_content(self.current_previewing_file)
        # messagebox.showinfo("插入成功", f"新的字幕行 (序号 {new_pysrt_index}) 已添加到末尾。") # Messagebox after refresh might be better
        self.logger.info(f"New subtitle item inserted for {self.current_previewing_file} and preview refreshed.")

    def update_preview_for_status(self, message: str):
        # This method might need to be rethought.
        # If it's for status messages, they could go to a status bar or a different label.
        # For now, let's adapt it to add text to the new scrollable frame, though this is not its final purpose.
        status_label = ctk.CTkLabel(self.subtitle_editor_scrollable_frame, text=message)
        status_label.pack(pady=2)
        self.apply_changes_button.configure(state="disabled")

    def on_individual_item_changed(self, event, item_gui_index, part_changed):
        # item_gui_index is the index in self.subtitle_entry_widgets
        # This function enables the apply_changes_button.
        # Actual data model update happens in apply_preview_changes.
        if not self.preview_edited:
            self.preview_edited = True
            self.apply_changes_button.configure(state="normal")
        self.logger.debug(f"Subtitle item GUI index {item_gui_index} part '{part_changed}' changed by user.")

    def _parse_srt_time_string(self, time_str):
        try:
            if isinstance(time_str, pysrt.SubRipTime): # Already correct type
                return time_str
            
            main_parts, ms_str = time_str.split(',')
            h_str, m_str, s_str = main_parts.split(':')
            
            hours = int(h_str)
            minutes = int(m_str)
            seconds = int(s_str)
            milliseconds = int(ms_str)
            
            if not (0 <= hours <= 99 and 0 <= minutes <= 59 and 0 <= seconds <= 59 and 0 <= milliseconds <= 999):
                raise ValueError("Time component out of valid range.")
                
            return pysrt.SubRipTime(hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds)
        except Exception as e: # Catches ValueError from int conversion, split errors, etc.
            self.logger.warning(f"Invalid time string format: '{time_str}'. Error: {e}")
            return None

    def apply_preview_changes(self):
        self.logger.info("Apply preview changes button clicked in ResultsPanel.")
        if not self.current_previewing_file:
            messagebox.showwarning("无预览", "当前没有文件正在预览。")
            return

        if not self.preview_edited:
            self.logger.info("No changes to apply to preview.")
            # It's possible edits were made then undone, making preview_edited true but values same.
            # For simplicity, if button is enabled, we assume intent to process.
            # Or, we could add a more robust "is_dirty" check by comparing with original data.
            # For now, if self.preview_edited is False, we return.
            return

        source_structured_data = self.generated_subtitle_data_map.get(self.current_previewing_file)
        if not source_structured_data:
            messagebox.showerror("错误", "未找到当前预览文件的原始结构化字幕数据。")
            self.logger.error(f"Apply changes: No source structured data for {self.current_previewing_file}")
            return

        if len(source_structured_data) != len(self.subtitle_entry_widgets):
            messagebox.showerror("内部错误", "UI条目数量与字幕数据不匹配。请重新预览文件以刷新编辑器。")
            self.logger.error(f"Apply changes: Mismatch len(structured_data)={len(source_structured_data)} vs len(widgets)={len(self.subtitle_entry_widgets)}")
            return

        new_validated_subs = []
        validation_failed = False

        for i, entry_widget_set in enumerate(self.subtitle_entry_widgets):
            original_item_index = entry_widget_set['item_index'] # Should be same as i

            start_time_str = entry_widget_set['start_entry'].get()
            parsed_start_time = self._parse_srt_time_string(start_time_str)
            if parsed_start_time is None:
                messagebox.showerror("时间格式错误", f"第 {i+1} 行的开始时间 '{start_time_str}' 格式无效。\n请使用 HH:MM:SS,mmm (例如 00:01:23,456)。")
                validation_failed = True
                break

            end_time_str = entry_widget_set['end_entry'].get()
            parsed_end_time = self._parse_srt_time_string(end_time_str)
            if parsed_end_time is None:
                messagebox.showerror("时间格式错误", f"第 {i+1} 行的结束时间 '{end_time_str}' 格式无效。\n请使用 HH:MM:SS,mmm。")
                validation_failed = True
                break

            if parsed_start_time >= parsed_end_time: # Use >= to prevent zero-duration subtitles from this check
                messagebox.showwarning("时间逻辑错误", f"第 {i+1} 行:\n开始时间 ({start_time_str}) 必须早于结束时间 ({end_time_str})。")
                self.logger.warning(f"Time logic error item {i+1}: start ({start_time_str}) >= end ({end_time_str})")
                validation_failed = True
                break
            
            if i > 0 and len(new_validated_subs) > 0: # Check against PREVIOUS item in the NEW list
                prev_item_end_time = new_validated_subs[-1].end
                if parsed_start_time < prev_item_end_time:
                     messagebox.showwarning("时间重叠警告", f"第 {i+1} 行的开始时间 ({start_time_str}) \n与上一行已验证的结束时间 ({str(prev_item_end_time)}) 重叠。")
                     self.logger.warning(f"Time overlap for item {i+1} with previous validated item.")
                     # Allow overlap for now, but log it. Could be a strict failure.
                     # validation_failed = True; break

            text_from_var = entry_widget_set['text_entry_var'].get()
            actual_text = text_from_var.replace(' \\n ', '\n')

            # Create a new SubRipItem for the validated data
            # Preserve original index if pysrt uses it internally, otherwise it's just for sequence
            new_item = pysrt.SubRipItem(
                index=(source_structured_data[original_item_index].index
                       if hasattr(source_structured_data[original_item_index], 'index')
                       else i + 1), # pysrt items are 1-indexed if from file
                start=parsed_start_time,
                end=parsed_end_time,
                text=actual_text
            )
            new_validated_subs.append(new_item)

        if not validation_failed:
            self.generated_subtitle_data_map[self.current_previewing_file] = new_validated_subs
            self.preview_edited = False
            self.apply_changes_button.configure(state="disabled")
            
            # Refresh the preview to show formatted times and reflect changes
            self.set_main_preview_content(self.current_previewing_file)

            messagebox.showinfo("成功", f"对 {os.path.basename(self.current_previewing_file)} 的更改已应用并保存在内存中。")
            self.logger.info(f"Changes applied to internal data for {self.current_previewing_file}. Processed {len(new_validated_subs)} entries.")
        else:
            self.logger.warning(f"Validation failed while applying changes for {self.current_previewing_file}. Changes not saved.")
            # Do not disable button or reset preview_edited, allow user to fix.

    def export_current_preview(self):
        if not self.current_previewing_file or not self.generated_subtitle_data_map.get(self.current_previewing_file):
            messagebox.showwarning("无数据", "没有可导出的字幕数据，或当前选中的文件没有成功生成字幕。")
            return
        
        # Delegate to MainWindow to handle the export logic as it knows the output_dir
        if hasattr(self.master, 'export_single_file'):
            self.master.export_single_file(
                self.current_previewing_file,
                self.generated_subtitle_data_map[self.current_previewing_file],
                self.export_format_var.get().lower()
            )

    def export_all_successful(self):
        # Delegate to MainWindow
        if hasattr(self.master, 'export_all_successful_subtitles_from_results_panel'):
             self.master.export_all_successful_subtitles_from_results_panel(
                 self.export_format_var.get().lower()
             )
    
    def update_export_buttons_state(self, can_export_current, can_export_all):
        self.export_button.configure(state="normal" if can_export_current else "disabled")
        self.export_all_button.configure(state="normal" if can_export_all else "disabled")

    def get_export_format(self):
        return self.export_format_var.get().lower()