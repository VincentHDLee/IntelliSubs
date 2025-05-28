import customtkinter as ctk
import os

class CombinedFileStatusPanel(ctk.CTkScrollableFrame):
    def __init__(self, master, logger, **kwargs):
        super().__init__(master, **kwargs)
        self.logger = logger
        self.file_entries = {}  # Store references to row frames and widgets: {file_path: {row_frame, name_label, status_label, preview_button}}
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
        row_frame.pack(fill="x", pady=(2,0), padx=2) # Use pack for rows within scrollable frame

        # Configure columns for the row_frame: 0: filename (weight 3), 1: status (weight 1), 2: button (weight 0)
        row_frame.grid_columnconfigure(0, weight=3)
        row_frame.grid_columnconfigure(1, weight=1)
        row_frame.grid_columnconfigure(2, weight=0)

        name_label = ctk.CTkLabel(row_frame, text=base_name, anchor="w")
        name_label.grid(row=0, column=0, padx=5, pady=2, sticky="ew")

        status_label = ctk.CTkLabel(row_frame, text="待处理", anchor="w")
        status_label.grid(row=0, column=1, padx=5, pady=2, sticky="ew")

        preview_button = ctk.CTkButton(row_frame, text="预览", width=60, state="disabled")
        preview_button.grid(row=0, column=2, padx=5, pady=2, sticky="e")

        self.file_entries[file_path] = {
            "row_frame": row_frame,
            "name_label": name_label,
            "status_label": status_label,
            "preview_button": preview_button,
            "bg_color": bg_color # Store original color if needed for hover effects etc.
        }
        self.logger.info(f"Added file to CombinedPanel: {base_name}")

    def update_file_status(self, file_path, status, error_message=None, processing_done=False):
        if file_path not in self.file_entries:
            self.logger.error(f"Cannot update status for {file_path}, not found in CombinedFileStatusPanel.")
            return

        entry = self.file_entries[file_path]
        display_status = status
        status_text_color = "white" # Default or based on theme

        if status == "错误" and error_message:
            display_status = f"错误: {error_message[:30]}..." if len(error_message) > 30 else f"错误: {error_message}"
            status_text_color = "red"
        elif status == "完成":
            status_text_color = "green"
        elif status == "处理中...":
            status_text_color = "orange"
        
        entry["status_label"].configure(text=display_status, text_color=status_text_color)
        
        if processing_done and status == "完成":
            entry["preview_button"].configure(state="normal")
        else:
            entry["preview_button"].configure(state="disabled")
        
        self.logger.info(f"Updated status for {os.path.basename(file_path)} to {display_status}")

    def set_preview_button_callback(self, file_path, callback):
        if file_path not in self.file_entries:
            self.logger.error(f"Cannot set preview callback for {file_path}, not found.")
            return
        entry = self.file_entries[file_path]
        entry["preview_button"].configure(command=callback)
        # State of preview button is handled by update_file_status based on '完成' status

    def clear_files(self):
        for file_path in list(self.file_entries.keys()): # Iterate over a copy of keys
            entry = self.file_entries.pop(file_path)
            entry["row_frame"].destroy()
        self._current_color_index = 0 # Reset color index
        self.logger.info("Cleared all files from CombinedFileStatusPanel.")

    def get_all_file_paths(self):
        return list(self.file_entries.keys())

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