# Base class for subtitle formatters
from abc import ABC, abstractmethod
import logging

class BaseSubtitleFormatter(ABC):
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger if logger else logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def format_subtitles(self, subtitle_entries: list) -> str:
        """
        Formats a list of subtitle entries into a specific subtitle file format string.

        Args:
            subtitle_entries (list): A list of dictionaries, where each dictionary
                                     represents a subtitle entry.
                                     Example: {"text": "Hello\nWorld", "start": 0.5, "end": 2.8}

        Returns:
            str: A string containing the formatted subtitle data.
        """
        pass

    def save_subtitles(self, subtitle_entries: list, output_path: str, encoding: str = "utf-8"):
        """
        Formats and saves the subtitle entries to a file.

        Args:
            subtitle_entries (list): List of subtitle entries.
            output_path (str): Path to save the subtitle file.
            encoding (str): File encoding to use (default: "utf-8").
        """
        formatted_content = self.format_subtitles(subtitle_entries)
        try:
            with open(output_path, 'w', encoding=encoding) as f:
                f.write(formatted_content)
            self.logger.info(f"Subtitles successfully saved to {output_path} with encoding {encoding}")
        except Exception as e:
            self.logger.error(f"Error saving subtitles to {output_path}: {e}", exc_info=True)
            raise # Re-raise the exception for the caller to handle