# TXT Subtitle Formatter
from .base_formatter import BaseSubtitleFormatter
import logging
import pysrt

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
            subtitle_entries (list): List of pysrt.SubRipItem objects.

        Returns:
            str: Plain text formatted string.
        """
        txt_content = []
        for entry in subtitle_entries:
            if not isinstance(entry, pysrt.SubRipItem):
                self.logger.warning(f"TxtFormatter: Entry is not a SubRipItem: {type(entry)}. Skipping.")
                continue
            
            # SubRipItem should always have a 'text' attribute, even if it's an empty string.
            # No explicit hasattr check needed after isinstance check if we rely on pysrt.SubRipItem structure.
            # However, if a SubRipItem could somehow be malformed without a text attr (unlikely),
            # a hasattr check or try-except for AttributeError would be more robust.
            # For now, directly accessing assuming valid SubRipItem.
            text = entry.text
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