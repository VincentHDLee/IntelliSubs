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