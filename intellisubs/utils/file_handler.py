# File Handling Utilities
import os
import shutil # For operations like copy, move
import logging

class FileHandler:
    def __init__(self, logger: logging.Logger = None):
        """
        Initializes the FileHandler. Accepts a logger instance.
        """
        self.logger = logger if logger else logging.getLogger(__name__)

    def ensure_dir_exists(self, dir_path: str):
        """Ensures that a directory exists, creating it if necessary."""
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True) # exist_ok=True handles race conditions
                self.logger.info(f"Directory created: {dir_path}")
            except Exception as e:
                self.logger.error(f"Error creating directory {dir_path}: {e}", exc_info=True)
                raise
        else:
            if not os.path.isdir(dir_path):
                self.logger.error(f"Path exists but is not a directory: {dir_path}")
                raise NotADirectoryError(f"Path exists but is not a directory: {dir_path}")


    def get_filename(self, file_path: str, with_extension: bool = True) -> str:
        """Extracts the filename from a full path."""
        base = os.path.basename(file_path)
        if with_extension:
            return base
        return os.path.splitext(base)[0]

    def get_file_extension(self, file_path: str) -> str:
        """Extracts the file extension (including the dot)."""
        return os.path.splitext(file_path)[1]

    def safe_delete_file(self, file_path: str):
        """Safely deletes a file, handling potential errors."""
        try:
            if os.path.exists(file_path):
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    self.logger.info(f"File deleted: {file_path}")
                else:
                    self.logger.warning(f"Path is not a file, cannot delete: {file_path}")
            else:
                self.logger.warning(f"File not found, cannot delete: {file_path}")
        except Exception as e:
            self.logger.error(f"Error deleting file {file_path}: {e}", exc_info=True)
            # Decide if to raise or just log

    # Add other common file operations as needed, e.g., copy_file, move_file, list_files_in_dir etc.

if __name__ == '__main__':
    # Example Usage
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    test_logger = logging.getLogger("TestFileHandler")
    fh = FileHandler(logger=test_logger)

    test_dir = "temp_test_dir_fh"
    fh.ensure_dir_exists(test_dir)
    
    test_file = os.path.join(test_dir, "example.txt")
    with open(test_file, "w") as f:
        f.write("Hello")
        
    test_logger.info(f"Filename: {fh.get_filename(test_file)}")
    test_logger.info(f"Filename (no ext): {fh.get_filename(test_file, with_extension=False)}")
    test_logger.info(f"Extension: {fh.get_file_extension(test_file)}")
    
    fh.safe_delete_file(test_file)
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir) # Clean up test directory
        test_logger.info(f"Test directory deleted: {test_dir}")