# SRT Subtitle Formatter
from .base_formatter import BaseSubtitleFormatter
# import pysrt # Placeholder for actual pysrt usage if preferred over manual formatting

def format_time_srt(seconds: float) -> str:
    """Converts seconds to SRT time format HH:MM:SS,mmm"""
    millis = int((seconds - int(seconds)) * 1000)
    seconds = int(seconds)
    mins = seconds // 60
    seconds %= 60
    hours = mins // 60
    mins %= 60
    return f"{hours:02d}:{mins:02d}:{seconds:02d},{millis:03d}"
def parse_srt_time(time_str: str) -> float:
    """Converts SRT time format HH:MM:SS,mmm to seconds."""
    if not time_str or not isinstance(time_str, str):
        raise ValueError(f"Invalid time string input: {time_str}")

    parts = time_str.split(':')
    if len(parts) != 3:
        raise ValueError(f"Invalid time string format (HH:MM:SS,mmm): {time_str}")
    
    try:
        hours = int(parts[0])
        minutes = int(parts[1])
        sec_millis_parts = parts[2].split(',')
        if len(sec_millis_parts) != 2:
            raise ValueError(f"Invalid seconds,milliseconds format: {parts[2]}")
        
        seconds = int(sec_millis_parts[0])
        milliseconds = int(sec_millis_parts[1])
        
        total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
        return total_seconds
    except ValueError as e:
        # Re-raise with more context or log
        raise ValueError(f"Error parsing time string '{time_str}': {e}")

class SRTFormatter(BaseSubtitleFormatter):
    def __init__(self, logger=None):
        super().__init__(logger)
        self.logger.info("SRTFormatter initialized.")

    def format_subtitles(self, subtitle_entries: list) -> str:
        """
        Formats subtitle entries into SRT format.

        Args:
            subtitle_entries (list): List of subtitle entry dicts.
                                     Example: {"text": "Line1\nLine2", "start": 0.5, "end": 2.8}

        Returns:
            str: SRT formatted string.
        """
        srt_content = []
        for i, entry in enumerate(subtitle_entries):
            if not all(k in entry for k in ["text", "start", "end"]):
                self.logger.warning(f"Skipping invalid subtitle entry at index {i}: {entry}")
                continue
            
            start_time_str = format_time_srt(entry["start"])
            end_time_str = format_time_srt(entry["end"])
            text = entry["text"]

            srt_content.append(str(i + 1))
            srt_content.append(f"{start_time_str} --> {end_time_str}")
            srt_content.append(text)
            srt_content.append("")  # Blank line separator
        
        return "\n".join(srt_content)

    def parse_srt_string(self, srt_string: str) -> list:
        """
        Parses an SRT formatted string into a list of subtitle entries.

        Args:
            srt_string (str): The SRT formatted string.

        Returns:
            list: A list of subtitle entry dicts.
                  Example: [{"text": "Line1\nLine2", "start": 0.5, "end": 2.8}, ...]
                  Returns empty list if parsing fails or string is empty.
        """
        if not srt_string or not isinstance(srt_string, str):
            self.logger.warning("parse_srt_string: Input SRT string is empty or invalid.")
            return []

        entries = []
        # Normalize line endings and split by double newlines (common block separator)
        normalized_string = srt_string.replace('\r\n', '\n').replace('\r', '\n')
        blocks = normalized_string.strip().split('\n\n')

        # import re # Not strictly needed for this line-by-line approach

        for i, block_text in enumerate(blocks):
            block_text = block_text.strip()
            if not block_text:
                continue

            lines = block_text.split('\n')
            if len(lines) < 2:
                self.logger.warning(f"Skipping malformed SRT block #{i+1} (not enough lines): '{block_text[:100]}...'")
                continue

            try:
                time_line_index = -1
                potential_time_line = ""

                if "-->" in lines[0]:
                    time_line_index = 0
                    potential_time_line = lines[0]
                elif len(lines) > 1 and "-->" in lines[1]:
                    time_line_index = 1
                    potential_time_line = lines[1]
                else:
                    self.logger.warning(f"Skipping malformed SRT block #{i+1} (time string '-->' not found in expected lines): '{block_text[:100]}...'")
                    continue

                time_parts = potential_time_line.split('-->')
                if len(time_parts) != 2:
                    self.logger.warning(f"Skipping malformed SRT block #{i+1} (invalid time components '{potential_time_line}'): '{block_text[:100]}...'")
                    continue

                start_time_str = time_parts[0].strip()
                end_time_str = time_parts[1].strip()

                start_time = parse_srt_time(start_time_str) # Uses the function defined at module level
                end_time = parse_srt_time(end_time_str)

                if start_time >= end_time:
                    self.logger.warning(f"Skipping SRT block #{i+1} (start_time {start_time_str} >= end_time {end_time_str}): '{block_text[:100]}...'")
                    continue
                
                text_lines = lines[time_line_index + 1:]
                if not text_lines:
                    self.logger.warning(f"Skipping SRT block #{i+1} (no text found after time string): '{block_text[:100]}...'")
                    continue
                
                text = "\n".join(text_lines).strip()
                if not text:
                    self.logger.warning(f"Skipping SRT block #{i+1} (text is empty): '{block_text[:100]}...'")
                    continue

                entries.append({
                    "start": start_time,
                    "end": end_time,
                    "text": text
                })
            except ValueError as ve:
                self.logger.warning(f"Skipping SRT block #{i+1} due to parsing error (ValueError: {ve}): '{block_text[:100]}...'")
                continue
            except Exception as e:
                self.logger.error(f"Unexpected error processing SRT block #{i+1} ('{block_text[:100]}...'): {e}", exc_info=True)
                continue
        
        if not entries and srt_string.strip():
            self.logger.warning("SRT string parsing resulted in no valid entries. The string might be malformed or contain only invalid blocks.")
        elif entries:
            self.logger.info(f"Successfully parsed {len(entries)} SRT entries.")
            
        return entries

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