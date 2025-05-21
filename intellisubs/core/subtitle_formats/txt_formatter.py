# TXT Subtitle Formatter
from .base_formatter import BaseSubtitleFormatter
import logging

class TxtFormatter(BaseSubtitleFormatter):
    def __init__(self, logger: logging.Logger = None):
        super().__init__(logger)
        self.logger.info("TxtFormatter initialized.")

    def format_subtitles(self, subtitle_entries: list) -> str:
        """
        Formats subtitle entries into a plain text format.
        Each subtitle entry's text will be on a new line.
        Timestamps are ignored in this format.

        Args:
            subtitle_entries (list): List of subtitle entry dicts.
                                     Example: {"text": "Line1\nLine2", "start": 0.5, "end": 2.8}

        Returns:
            str: Plain text formatted string.
        """
        txt_content = []
        for i, entry in enumerate(subtitle_entries):
            if "text" not in entry:
                self.logger.warning(f"Skipping invalid TXT entry at index {i}: {entry} (missing 'text')")
                continue
            
            # Text might contain newlines from segmenter, which is fine for TXT
            text = entry["text"]
            txt_content.append(text)
            
        return "\n".join(txt_content)

if __name__ == '__main__':
    # Example Usage
    logging.basicConfig(level=logging.DEBUG)
    logger_instance = logging.getLogger("TestTxtFormatter")
    formatter = TxtFormatter(logger=logger_instance)
    
    test_entries = [
        {"text": "こんにちは、皆さん。", "start": 0.0, "end": 1.5},
        {"text": "元気ですか。\nはい、元気です。", "start": 2.0, "end": 4.0},
        {"text": "これはテストです。", "start": 4.5, "end": 5.5},
        {"start": 6.0, "end": 7.0} # Invalid entry
    ]
    
    formatted_txt = formatter.format_subtitles(test_entries)
    print("--- Formatted TXT ---")
    print(formatted_txt)

    # Example for saving
    # output_file = "example_output.txt"
    # formatter.save_subtitles(test_entries, output_file)
    # print(f"\nFormatted TXT saved to {output_file}")
    # try:
    #     with open(output_file, 'r', encoding='utf-8') as f:
    #         print("\nContent from file:")
    #         print(f.read())
    # except FileNotFoundError:
    #     print(f"\nFile {output_file} was not created.")