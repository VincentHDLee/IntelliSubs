# SRT Subtitle Formatter
from .base_formatter import BaseSubtitleFormatter
import pysrt

# Module-level helper functions format_time_srt and parse_srt_time are no longer needed
# as pysrt.SubRipTime objects handle their own string conversion, and pysrt.from_string handles parsing.

class SRTFormatter(BaseSubtitleFormatter):
    def __init__(self, logger=None):
        super().__init__(logger)
        self.logger.info("SRTFormatter initialized.")

    def format_subtitles(self, subtitle_entries: list) -> str:
        """
        Formats subtitle entries into SRT format.

        Args:
            subtitle_entries (list): List of pysrt.SubRipItem objects.

        Returns:
            str: SRT formatted string.
        """
        srt_content = []
        for entry in subtitle_entries: # No need for enumerate(i) if using entry.index
            if not isinstance(entry, pysrt.SubRipItem):
                self.logger.warning(f"SRTFormatter: Encountered an entry that is not a SubRipItem: {type(entry)}. Skipping.")
                continue
            
            # pysrt.SubRipItem objects inherently have start, end, text, and index attributes.
            start_time_str = str(entry.start) # pysrt.SubRipTime.__str__ gives "HH:MM:SS,mmm"
            end_time_str = str(entry.end)
            text_content = entry.text

            srt_content.append(str(entry.index))
            srt_content.append(f"{start_time_str} --> {end_time_str}")
            srt_content.append(text_content)
            srt_content.append("")  # Blank line separator
        
        return "\n".join(srt_content).strip() # Add strip() to remove trailing newline if any

    def parse_srt_string(self, srt_string: str) -> list:
        """
        Parses an SRT formatted string into a list of subtitle entries.

        Args:
            srt_string (str): The SRT formatted string.

        Returns:
            list: A list of pysrt.SubRipItem objects.
                  Returns empty list if parsing fails or string is empty.
        """
        if not srt_string or not isinstance(srt_string, str) or not srt_string.strip():
            self.logger.warning("parse_srt_string: Input SRT string is empty or invalid.")
            return []
        
        try:
            # pysrt.from_string handles various line endings and parsing complexities.
            # It raises pysrt.Error if parsing fails completely.
            # It returns a SubRipFile, which is a list-like object of SubRipItems.
            subs = pysrt.from_string(srt_string, error_handling=pysrt.ERROR_LOG) # Log errors but try to parse
            
            # Filter out any items that might be None or invalid if strict parsing fails but returns partial
            # हालांकि, pysrt.from_string 通常会引发错误或返回有效的 SubRipFile
            valid_items = [item for item in subs if isinstance(item, pysrt.SubRipItem)]
            
            if not valid_items and srt_string.strip(): # If string wasn't empty but no items parsed
                 if subs. πολλά_λάθη: # Check if pysrt logged errors
                     self.logger.warning(f"SRT string parsing by pysrt resulted in no valid entries, but pysrt logged {len(subs.πολλά_λάθη)} errors.")
                 else:
                     self.logger.warning("SRT string parsing by pysrt resulted in no valid entries. String might be severely malformed.")
            elif valid_items:
                 self.logger.info(f"Successfully parsed {len(valid_items)} SRT entries using pysrt.")

            return valid_items
        except pysrt.Error as e: # Catch pysrt specific parsing errors
            self.logger.error(f"Error parsing SRT string using pysrt: {e}", exc_info=True)
            return []
        except Exception as e: # Catch any other unexpected errors
            self.logger.error(f"Unexpected error during SRT string parsing with pysrt: {e}", exc_info=True)
            return []

    # Example using pysrt library (alternative implementation)
    # def format_subtitles_pysrt(self, subtitle_entries: list) -> str:
    #     subs = pysrt.SubRipFile()
    #     for i, entry in enumerate(subtitle_entries):
    #         sub = pysrt.SubRipItem(
    #             index=i + 1,
    #             start=pysrt.SubRipTime.from_ordinal(int(entry["start"] * 1000)),
    #             end=pysrt.SubRipTime.from_ordinal(int(entry["end"] * 1000)),
    #             text=entry["text"]
    #         )
    #         subs.append(sub)
    #     return str(subs)