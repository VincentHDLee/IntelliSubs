# File Handling Utilities
import os
import shutil # For operations like copy, move

class FileHandler:
    @staticmethod
    def ensure_dir_exists(dir_path: str):
        """Ensures that a directory exists, creating it if necessary."""
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True) # exist_ok=True handles race conditions
                print(f"Directory created: {dir_path}")
            except Exception as e:
                print(f"Error creating directory {dir_path}: {e}")
                raise
        else:
            if not os.path.isdir(dir_path):
                raise NotADirectoryError(f"Path exists but is not a directory: {dir_path}")


    @staticmethod
    def get_filename(file_path: str, with_extension: bool = True) -> str:
        """Extracts the filename from a full path."""
        base = os.path.basename(file_path)
        if with_extension:
            return base
        return os.path.splitext(base)[0]

    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """Extracts the file extension (including the dot)."""
        return os.path.splitext(file_path)[1]

    @staticmethod
    def safe_delete_file(file_path: str):
        """Safely deletes a file, handling potential errors."""
        try:
            if os.path.exists(file_path):
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"File deleted: {file_path}")
                else:
                    print(f"Warning: Path is not a file, cannot delete: {file_path}")
            else:
                print(f"Warning: File not found, cannot delete: {file_path}")
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
            # Decide if to raise or just log

    # Add other common file operations as needed, e.g., copy_file, move_file, list_files_in_dir etc.

if __name__ == '__main__':
    # Example Usage
    test_dir = "temp_test_dir"
    FileHandler.ensure_dir_exists(test_dir)
    
    test_file = os.path.join(test_dir, "example.txt")
    with open(test_file, "w") as f:
        f.write("Hello")
        
    print(f"Filename: {FileHandler.get_filename(test_file)}")
    print(f"Filename (no ext): {FileHandler.get_filename(test_file, with_extension=False)}")
    print(f"Extension: {FileHandler.get_file_extension(test_file)}")
    
    FileHandler.safe_delete_file(test_file)
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir) # Clean up test directory
        print(f"Test directory deleted: {test_dir}")