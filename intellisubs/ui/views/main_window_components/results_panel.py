import customtkinter as ctk
from tkinter import filedialog, messagebox
import os

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
        
        self.preview_textbox = ctk.CTkTextbox(self, wrap="word", state="disabled", height=120)
        self.preview_textbox.grid(row=1, column=0, padx=5, pady=(30,5), sticky="nsew") # Added pady top for label
        self.preview_textbox.bind("<KeyRelease>", self.on_preview_text_changed)

    def _create_export_controls(self):
        self.export_controls_frame = ctk.CTkFrame(self)
        self.export_controls_frame.grid(row=2, column=0, padx=5, pady=(5,5), sticky="ew")
        self.export_controls_frame.grid_columnconfigure(3, weight=1) # Allow "Export All" to push others left

        self.export_format_var = ctk.StringVar(value="SRT")
        self.export_options = ["SRT", "LRC", "ASS", "TXT"] # TODO: Get from config or core
        self.export_menu = ctk.CTkOptionMenu(self.export_controls_frame, variable=self.export_format_var, values=self.export_options)
        self.export_menu.grid(row=0, column=0, padx=(0,5), pady=5, sticky="w")

        self.apply_changes_button = ctk.CTkButton(self.export_controls_frame, text="应用更改", command=self.apply_preview_changes, state="disabled")
        self.apply_changes_button.grid(row=0, column=1, padx=5, pady=5, sticky="e")
        
        self.export_button = ctk.CTkButton(self.export_controls_frame, text="导出当前预览", command=self.export_current_preview, state="disabled")
        self.export_button.grid(row=0, column=2, padx=5, pady=5, sticky="e")

        self.export_all_button = ctk.CTkButton(self.export_controls_frame, text="导出所有成功", command=self.export_all_successful, state="disabled")
        self.export_all_button.grid(row=0, column=3, padx=(5,0), pady=5, sticky="e")

    def set_generated_data(self, data_map):
        self.generated_subtitle_data_map = data_map

    def clear_result_list(self):
        for widget in self.result_list_scrollable_frame.winfo_children():
            widget.destroy()
        self.preview_textbox.configure(state="normal")
        self.preview_textbox.delete("1.0", "end")
        self.preview_textbox.configure(state="disabled")
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
                command=lambda p=file_path, pt=preview_text_for_this_file: self.set_main_preview_content(pt, p)
            )
            preview_button.pack(side="right", padx=5, pady=2)
        
        # Auto-preview the first successful item or if it's the only one processed
        # This logic might be better handled by MainWindow after all results are added
        # if success and (not self.current_previewing_file or len(self.master.selected_file_paths_from_controls) == 1) : # master needs that attr
        #     self.set_main_preview_content(preview_text_for_this_file, file_path)


    def set_main_preview_content(self, content, file_path):
        self.preview_textbox.configure(state="normal")
        self.preview_textbox.delete("1.0", "end")
        if content:
            self.preview_textbox.insert("1.0", content)
        else:
            self.preview_textbox.insert("1.0", f"文件 {os.path.basename(file_path)} 未生成有效字幕预览。")
        # Keep editable: self.preview_textbox.configure(state="disabled") 
        self.preview_edited = False
        self.apply_changes_button.configure(state="disabled") # Disable until actual edit
        self.current_previewing_file = file_path
        
        if content and self.generated_subtitle_data_map.get(file_path):
             self.export_button.configure(state="normal")
        else:
             self.export_button.configure(state="disabled")

    def update_preview_for_status(self, message: str):
        self.preview_textbox.configure(state="normal")
        self.preview_textbox.insert("end", message)
        self.preview_textbox.see("end")
        self.preview_textbox.configure(state="disabled")
        self.apply_changes_button.configure(state="disabled")

    def on_preview_text_changed(self, event=None):
        if self.preview_textbox.cget("state") == "normal":
            if not self.preview_edited:
                self.preview_edited = True
                self.apply_changes_button.configure(state="normal")
                self.logger.debug("Preview text changed, Apply Changes button enabled.")

    def apply_preview_changes(self):
        self.logger.info("Apply preview changes button clicked in ResultsPanel.")
        if not self.current_previewing_file:
            messagebox.showwarning("无预览", "当前没有文件正在预览。")
            return

        if not self.preview_edited:
            self.logger.info("No changes to apply to preview.")
            return

        edited_text = self.preview_textbox.get("1.0", "end-1c")
        if not edited_text.strip():
            messagebox.showwarning("文本为空", "编辑后的字幕文本为空，无法应用。")
            return

        try:
            new_structured_data = self.workflow_manager.parse_subtitle_string(
                subtitle_string=edited_text, source_format="srt" # Assuming SRT for now
            )
            if new_structured_data is not None:
                self.generated_subtitle_data_map[self.current_previewing_file] = new_structured_data
                self.preview_edited = False
                self.apply_changes_button.configure(state="disabled")
                if not new_structured_data:
                    messagebox.showwarning("解析警告", f"编辑后的文本解析为空字幕列表。文件: {os.path.basename(self.current_previewing_file)}")
                    self.logger.warning(f"Edited text for {self.current_previewing_file} parsed into an empty subtitle list.")
                else:
                    messagebox.showinfo("成功", f"对 {os.path.basename(self.current_previewing_file)} 的更改已应用。")
                    self.logger.info(f"Changes applied to internal data for {self.current_previewing_file}. Parsed {len(new_structured_data)} entries.")
            else: # Should not happen based on parse_subtitle_string behavior
                 messagebox.showerror("应用失败", f"解析编辑后的字幕时返回意外结果。")
                 self.logger.error(f"Parsing edited text for {self.current_previewing_file} returned None unexpectedly.")

        except (ValueError, NotImplementedError) as e_parse:
            messagebox.showerror("解析错误", f"无法解析字幕文本: {e_parse}")
            self.logger.error(f"Error parsing edited text for {self.current_previewing_file}: {e_parse}", exc_info=True)
        except Exception as e:
            messagebox.showerror("应用错误", f"应用更改时发生未知错误: {e}")
            self.logger.error(f"Unknown error applying changes for {self.current_previewing_file}: {e}", exc_info=True)

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