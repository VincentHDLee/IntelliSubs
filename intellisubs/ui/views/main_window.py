# Main Window for IntelliSubs Application
import customtkinter as ctk
from tkinter import filedialog, messagebox # For dialogs

class MainWindow(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.app = master # Reference to the main IntelliSubsApp instance

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

        self.start_button = ctk.CTkButton(self.controls_frame, text="开始生成字幕", command=self.start_processing, state="disabled")
        self.start_button.grid(row=1, column=0, columnspan=3, padx=10, pady=(5,10), sticky="ew")

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
            # self.app.status_label.configure(text=f"已选择: {os.path.basename(path)}") # If app has status_label

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
        self.update_idletasks() # Ensure UI updates

        # Placeholder for calling self.app.workflow_manager.process_audio_to_subtitle
        # This should ideally run in a separate thread to avoid freezing the UI
        # For now, direct call (will freeze UI for long tasks)
        try:
            # output_format_for_preview = "txt" # Or a specific preview format from workflow
            # Simulating workflow call
            # status_msg, result_data = self.app.workflow_manager.process_audio_to_subtitle(
            #     self.current_file_path,
            #     output_format="srt" # Default format for processing, export can differ
            # )
            
            # Placeholder direct result
            status_msg = "Placeholder: 处理完成！"
            result_data = "1\n00:00:01,000 --> 00:00:03,000\n这是占位符字幕。\n\n2\n00:00:04,000 --> 00:00:06,000\n来自主窗口。"
            self.generated_subtitle_data = result_data # Store for export

            self.preview_textbox.configure(state="normal")
            self.preview_textbox.insert("end", f"{status_msg}\n---\n")
            if result_data:
                self.preview_textbox.insert("end", result_data)
                self.export_button.configure(state="normal")
            else:
                self.preview_textbox.insert("end", "未能生成字幕数据。")
            self.preview_textbox.configure(state="disabled")
            # self.app.status_label.configure(text=status_msg)

        except Exception as e:
            messagebox.showerror("处理错误", f"生成字幕时发生错误: {e}")
            self.preview_textbox.configure(state="normal")
            self.preview_textbox.insert("end", f"\n错误: {e}")
            self.preview_textbox.configure(state="disabled")
            # self.app.status_label.configure(text="处理失败")
        finally:
            self.start_button.configure(state="normal")
            self.browse_button.configure(state="normal")


    def export_subtitles(self):
        if not self.generated_subtitle_data:
            messagebox.showwarning("无数据", "没有可导出的字幕数据。请先生成字幕。")
            return

        export_format = self.export_format_var.get().lower()
        default_filename = f"{self.current_file_path}.{export_format}"
        
        file_types_map = {
            "srt": [("SubRip Subtitle", "*.srt")],
            "lrc": [("LyRiCs Subtitle", "*.lrc")],
            "ass": [("Advanced SubStation Alpha", "*.ass")],
            "txt": [("Text File", "*.txt")]
        }
        file_types = file_types_map.get(export_format, [("All files", "*.*")])

        save_path = filedialog.asksaveasfilename(
            title=f"导出为 {export_format.upper()}",
            initialfile=default_filename,
            defaultextension=f".{export_format}",
            filetypes=file_types
        )

        if save_path:
            try:
                # Here, ideally, we would re-format self.generated_subtitle_data if it's not already in the target format,
                # or if generated_subtitle_data was a more structured intermediate form.
                # For this placeholder, we assume self.generated_subtitle_data IS the SRT string.
                # A real implementation would call the appropriate formatter from workflow_manager or app.
                
                # Placeholder: If user wants different format, we'd need to re-process or re-format.
                # For now, just save what we have if it's SRT, or show error.
                final_data_to_save = ""
                if export_format == "srt" and self.generated_subtitle_data: # Assuming preview was SRT
                     final_data_to_save = self.generated_subtitle_data
                # elif export_format == "txt" and self.generated_subtitle_data: # Example for raw text
                #      final_data_to_save = self.generated_subtitle_data # if preview was just text
                else:
                    # This is where you'd call:
                    # status, final_data_to_save = self.app.workflow_manager.format_processed_data(self.intermediate_processed_data, export_format)
                    # For now, just a placeholder:
                    final_data_to_save = f"[{export_format.upper()}] Placeholder for: \n{self.generated_subtitle_data}"


                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(final_data_to_save)
                messagebox.showinfo("成功", f"字幕已导出到: {save_path}")
                # self.app.status_label.configure(text=f"已导出: {os.path.basename(save_path)}")
            except Exception as e:
                messagebox.showerror("导出错误", f"导出字幕时发生错误: {e}")
                # self.app.status_label.configure(text="导出失败")

if __name__ == '__main__':
    # For testing MainWindow independently
    # This requires IntelliSubsApp to be defined or a mock master
    class MockApp(ctk.CTk):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.title("MainWindow Test")
            self.geometry("800x600")
            # self.workflow_manager = None # Mock it if MainWindow methods use it
            # self.status_label = ctk.CTkLabel(self, text="Mock Status")
            # self.status_label.pack(side="bottom", fill="x")

    app_test = MockApp()
    main_frame = MainWindow(master=app_test)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)
    app_test.mainloop()