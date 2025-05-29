import customtkinter as ctk
import os

class CombinedFileStatusPanel(ctk.CTkScrollableFrame):
    STATUS_PENDING = "待处理"
    STATUS_PROCESSING_ASR = "ASR处理中..."
    STATUS_ASR_DONE = "ASR完成" # Ready for LLM
    STATUS_PROCESSING_LLM = "LLM增强中..."
    STATUS_LLM_DONE = "增强完成"
    STATUS_ERROR = "错误"
    STATUS_LLM_FAILED = "LLM增强失败"

    def __init__(self, master, logger, app_ref, on_file_removed_callback=None, **kwargs): # Added app_ref
        super().__init__(master, **kwargs)
        self.logger = logger
        self.app_ref = app_ref # Store app_ref to access global config and request LLM
        self.on_file_removed_callback = on_file_removed_callback
        # {file_path: {row_frame, name_label, status_label, generate_asr_button, preview_button, llm_enhance_button, remove_button}}
        self.file_entries = {}
        self._current_color_index = 0
        self.rainbow_colors = [
            "#FFCCCC", "#FFE5CC", "#FFFFCC", "#CCFFCC",  # Lighter Red, Orange, Yellow, Green
            "#CCE5FF", "#E5CCFF", "#F5CCFF"               # Lighter Blue, Indigo, Violet
        ]
        # Lighter pastel versions of rainbow colors for background
        # Original: ["#FF0000", "#FFA500", "#FFFF00", "#008000", "#00FFFF", "#0000FF", "#800080"]

        self.grid_columnconfigure(0, weight=1) # Ensure content within stretches

    def _get_next_bg_color(self):
        color = self.rainbow_colors[self._current_color_index]
        self._current_color_index = (self._current_color_index + 1) % len(self.rainbow_colors)
        return color

    def add_file(self, file_path):
        if file_path in self.file_entries:
            self.logger.warning(f"File {file_path} already in CombinedFileStatusPanel. Skipping.")
            return

        base_name = os.path.basename(file_path)
        bg_color = self._get_next_bg_color()

        row_frame = ctk.CTkFrame(self, fg_color=bg_color)
        row_frame.pack(fill="x", pady=(2,0), padx=2)

        # Configure columns: 0: filename (w3), 1: status (w2), 2: gen_asr_btn, 3: preview_btn, 4: llm_btn, 5: remove_btn (all w0)
        row_frame.grid_columnconfigure(0, weight=3) # Filename
        row_frame.grid_columnconfigure(1, weight=2) # Status
        row_frame.grid_columnconfigure(2, weight=0) # Generate ASR button
        row_frame.grid_columnconfigure(3, weight=0) # Preview button
        row_frame.grid_columnconfigure(4, weight=0) # LLM Enhance button
        row_frame.grid_columnconfigure(5, weight=0) # Remove button

        name_label = ctk.CTkLabel(row_frame, text=base_name, anchor="w")
        name_label.grid(row=0, column=0, padx=5, pady=2, sticky="ew")

        status_label = ctk.CTkLabel(row_frame, text=self.STATUS_PENDING, anchor="w")
        status_label.grid(row=0, column=1, padx=5, pady=2, sticky="ew")

        generate_asr_button = ctk.CTkButton(row_frame, text="生成ASR", width=80, state="normal",
                                             command=lambda p=file_path: self._request_single_file_asr(p))
        generate_asr_button.grid(row=0, column=2, padx=(5,2), pady=2, sticky="e") # New button

        # LLM Enhance button will now be at column 3
        llm_enhance_button = ctk.CTkButton(row_frame, text="LLM增强", width=80, state="disabled",
                                           command=lambda p=file_path: self._request_llm_enhancement(p))
        llm_enhance_button.grid(row=0, column=3, padx=2, pady=2, sticky="e")

        # Preview button will now be at column 4
        preview_button = ctk.CTkButton(row_frame, text="预览", width=60, state="disabled")
        preview_button.grid(row=0, column=4, padx=2, pady=2, sticky="e")
        
        remove_button = ctk.CTkButton(row_frame, text="X", width=25, fg_color="#D9534F", hover_color="#C9302C",
                                      command=lambda p=file_path: self._remove_file_entry(p))
        remove_button.grid(row=0, column=5, padx=(2,5), pady=2, sticky="e") # Adjusted column

        self.file_entries[file_path] = {
            "row_frame": row_frame,
            "name_label": name_label,
            "status_label": status_label,
            "generate_asr_button": generate_asr_button, # Added button
            "preview_button": preview_button,
            "llm_enhance_button": llm_enhance_button,
            "remove_button": remove_button,
            "bg_color": bg_color
        }
        self.logger.info(f"Added file to CombinedPanel: {base_name}")

    def update_file_status(self, file_path, status, error_message=None, processing_done=False):
        if file_path not in self.file_entries:
            self.logger.error(f"Cannot update status for {file_path}, not found in CombinedFileStatusPanel.")
            return

        entry = self.file_entries[file_path]
        display_status = status
        status_text_color = "white" # Default or based on theme
        generate_asr_button_state = "normal"
        generate_asr_button_text = "生成ASR" # Default text
        llm_enhance_button_text = "LLM增强" # Fixed text
        preview_button_state = "disabled"
        llm_enhance_button_state = "disabled"
        remove_button_state = "normal" # Default state for remove button


        # Determine button states and colors based on status
        if status == self.STATUS_ERROR or status == self.STATUS_LLM_FAILED:
            actual_error_message = error_message if error_message else "未知错误"
            display_status = f"错误: {actual_error_message[:30]}..." if len(actual_error_message) > 30 else f"错误: {actual_error_message}"
            status_text_color = "red"
            generate_asr_button_state = "normal" # Allow retry ASR on error
            # generate_asr_button_text is "生成ASR" (default)
            preview_button_state = "disabled"
            # LLM button should be enabled if ASR had an error but LLM is configured, to allow retrying enhancement on potentially existing (old) ASR data
            if self.app_ref and self.app_ref.config.get("llm_enabled") and \
               self.app_ref.config.get("llm_api_key") and \
               self.app_ref.config.get("llm_base_url") and \
               self.app_ref.config.get("llm_model_name"):
                llm_enhance_button_state = "normal"
            else:
                llm_enhance_button_state = "disabled"
            remove_button_state = "normal"
        elif status == self.STATUS_ASR_DONE or status == self.STATUS_LLM_DONE: # Covers ASR_DONE and LLM_DONE
            status_text_color = "green" if status == self.STATUS_ASR_DONE else "#00A000"
            generate_asr_button_state = "normal" # Allow re-running ASR even if done
            preview_button_state = "normal"
            if self.app_ref and self.app_ref.config.get("llm_enabled") and \
               self.app_ref.config.get("llm_api_key") and \
               self.app_ref.config.get("llm_base_url") and \
               self.app_ref.config.get("llm_model_name"):
                llm_enhance_button_state = "normal" # Always enabled if ASR done & LLM configured
            else:
                llm_enhance_button_state = "disabled"
            remove_button_state = "normal"
        elif status == self.STATUS_PROCESSING_ASR:
            status_text_color = "orange"
            generate_asr_button_state = "disabled" # Disabled during ASR processing
            generate_asr_button_text = "ASR中..."
            preview_button_state = "disabled"
            llm_enhance_button_state = "disabled"
            remove_button_state = "disabled" # Disable remove during ASR processing
        elif status == self.STATUS_PROCESSING_LLM:
            status_text_color = "orange"
            generate_asr_button_state = "normal" # ASR button should be re-enabled if LLM is processing or has failed
            # generate_asr_button_text is "生成ASR" (default)
            preview_button_state = "disabled" # Disable preview while LLM enhancing
            llm_enhance_button_state = "disabled" # LLM button is disabled during its own processing
            llm_enhance_button_text = "增强中..." # Text changes during processing
            remove_button_state = "disabled" # Disable remove during LLM processing
        elif status == self.STATUS_PENDING:
            generate_asr_button_state = "normal"
            # generate_asr_button_text is "生成ASR" (default)
            preview_button_state = "disabled"
            llm_enhance_button_state = "disabled"
            remove_button_state = "normal"

        entry["status_label"].configure(text=display_status, text_color=status_text_color)
        entry["generate_asr_button"].configure(text=generate_asr_button_text, state=generate_asr_button_state)
        entry["preview_button"].configure(state=preview_button_state)
        entry["llm_enhance_button"].configure(text=llm_enhance_button_text, state=llm_enhance_button_state)
        entry["remove_button"].configure(state=remove_button_state)
        
        self.logger.info(f"Updated status for {os.path.basename(file_path)} to {display_status}. ASR Btn: {generate_asr_button_state}({generate_asr_button_text}), Preview Btn: {preview_button_state}, LLM Btn: {llm_enhance_button_state}, Remove Btn: {remove_button_state}")

    def set_preview_button_callback(self, file_path, callback):
        if file_path not in self.file_entries:
            self.logger.error(f"Cannot set preview callback for {file_path}, not found.")
            return
        entry = self.file_entries[file_path]
        entry["preview_button"].configure(command=callback)
        # State of preview button is handled by update_file_status based on '完成' status

    def clear_files(self):
        for file_path in list(self.file_entries.keys()):
            entry = self.file_entries.pop(file_path) # Remove from dict
            entry["row_frame"].destroy() # Destroy UI element
        self._current_color_index = 0 # Reset color index
        self.logger.info("Cleared all files from CombinedFileStatusPanel.")

    def get_all_file_paths(self):
        return list(self.file_entries.keys())

    def _remove_file_entry(self, file_path):
        if file_path not in self.file_entries:
            self.logger.warning(f"Attempted to remove non-existent file {file_path} from CombinedPanel.")
            return
        
        entry_to_remove = self.file_entries.pop(file_path)
        entry_to_remove["row_frame"].destroy()
        self.logger.info(f"Removed file from CombinedPanel: {os.path.basename(file_path)}")

        if self.on_file_removed_callback:
            self.on_file_removed_callback(file_path)
    
    def _request_llm_enhancement(self, file_path: str):
        if self.app_ref and hasattr(self.app_ref, 'request_llm_enhancement_for_file'):
            self.logger.info(f"Requesting LLM enhancement for file: {file_path}")
            # Disable button immediately to prevent double clicks. Text will be "增强中..." via update_file_status.
            if file_path in self.file_entries:
                # update_file_status will handle text and state for STATUS_PROCESSING_LLM
                # No need to set text here directly, it will be overridden.
                # Only ensure status is updated to trigger the visual change.
                self.update_file_status(file_path, self.STATUS_PROCESSING_LLM) # This will set button text to "增强中..." and disable it
            self.app_ref.request_llm_enhancement_for_file(file_path) # Call the actual enhancement
        else:
            self.logger.error(f"Cannot request LLM enhancement for {file_path}: app_ref or callback method not found.")

    def _request_single_file_asr(self, file_path: str):
        if self.app_ref and hasattr(self.app_ref, 'request_asr_for_single_file'):
            self.logger.info(f"Requesting single file ASR for: {file_path}")
            # Update UI for this specific file to show "Processing ASR..."
            if file_path in self.file_entries:
                entry = self.file_entries[file_path]
                entry["generate_asr_button"].configure(state="disabled", text="ASR中...")
                entry["status_label"].configure(text=self.STATUS_PROCESSING_ASR, text_color="orange")
                # Disable other action buttons for this file
                entry["preview_button"].configure(state="disabled")
                entry["llm_enhance_button"].configure(state="disabled")
                entry["remove_button"].configure(state="disabled") # Disable remove button during ASR
            
            self.app_ref.request_asr_for_single_file(file_path)
        else:
            has_callback = False
            app_ref_type_str = "None"
            if self.app_ref:
                app_ref_type_str = str(type(self.app_ref))
                has_callback = hasattr(self.app_ref, 'request_asr_for_single_file')
            self.logger.error(f"Cannot request single file ASR for {file_path}: app_ref type is {app_ref_type_str}, hasattr(request_asr_for_single_file): {has_callback}.")


if __name__ == '__main__':
    # Example Usage
    class App(ctk.CTk):
        def __init__(self):
            super().__init__()
            self.title("Combined Panel Test")
            self.geometry("700x500")

            # Mock logger
            import logging
            self.logger = logging.getLogger("TestLogger")
            self.logger.setLevel(logging.DEBUG)
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)

            self.combined_panel = CombinedFileStatusPanel(self, logger=self.logger, label_text="文件处理状态")
            self.combined_panel.pack(fill="both", expand=True, padx=10, pady=10)

            self.controls_frame = ctk.CTkFrame(self)
            self.controls_frame.pack(fill="x", padx=10, pady=(0,10))

            add_button = ctk.CTkButton(self.controls_frame, text="Add File", command=self.add_test_file)
            add_button.pack(side="left", padx=5)
            
            update_button = ctk.CTkButton(self.controls_frame, text="Update Status (Success)", command=self.update_test_file_success)
            update_button.pack(side="left", padx=5)

            update_err_button = ctk.CTkButton(self.controls_frame, text="Update Status (Error)", command=self.update_test_file_error)
            update_err_button.pack(side="left", padx=5)

            clear_button = ctk.CTkButton(self.controls_frame, text="Clear All", command=self.clear_all_files)
            clear_button.pack(side="left", padx=5)
            
            self.test_file_counter = 0
            self.current_test_file_path = None

        def add_test_file(self):
            self.test_file_counter += 1
            file_path = f"/path/to/test_video_file_{self.test_file_counter}.mp4"
            self.current_test_file_path = file_path
            self.combined_panel.add_file(file_path)
            self.combined_panel.set_preview_button_callback(file_path, lambda p=file_path: self.logger.info(f"Preview for {p} clicked!"))

        def update_test_file_success(self):
            if self.current_test_file_path:
                self.combined_panel.update_file_status(self.current_test_file_path, "完成", processing_done=True)
        
        def update_test_file_error(self):
            if self.current_test_file_path:
                self.combined_panel.update_file_status(self.current_test_file_path, "错误", "ASR failed due to reasons.", processing_done=True)


        def clear_all_files(self):
            self.combined_panel.clear_files()
            self.test_file_counter = 0
            self.current_test_file_path = None


    app = App()
    app.mainloop()