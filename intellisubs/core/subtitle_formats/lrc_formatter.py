# LRC Subtitle Formatter
from .base_formatter import BaseSubtitleFormatter
import math

def format_time_lrc(seconds: float) -> str:
    """Converts seconds to LRC time format MM:SS.xx"""
    if seconds < 0: seconds = 0.0 # Guard against negative time
    minutes = math.floor(seconds / 60)
    remaining_seconds = seconds % 60
    hundredths = math.floor((remaining_seconds - math.floor(remaining_seconds)) * 100)
    return f"{int(minutes):02d}:{math.floor(remaining_seconds):02d}.{int(hundredths):02d}"

class LRCFormatter(BaseSubtitleFormatter):
    def format_subtitles(self, subtitle_entries: list) -> str:
        """
        Formats subtitle entries into LRC format.
        LRC typically has one line of text per timestamp. If an entry has multiple
        lines (e.g., "Line1\nLine2"), they might be output as separate LRC lines
        with the same start timestamp, or the formatter might choose to only use
        the first line. For this basic version, we'll take the first line if multiple.

        Args:
            subtitle_entries (list): List of subtitle entry dicts.
                                     Example: {"text": "Line1\nLine2", "start": 0.5, "end": 2.8}

        Returns:
            str: LRC formatted string.
        """
        lrc_content = []
        # Add some common LRC headers (optional, depends on player compatibility)
        # lrc_content.append("[ar:Artist Name]") # Placeholder
        # lrc_content.append("[ti:Track Title]") # Placeholder
        # lrc_content.append("[al:Album Name]") # Placeholder
        # lrc_content.append("[length:MM:SS]") # Placeholder, can be calculated

        for entry in subtitle_entries:
            if not all(k in entry for k in ["text", "start"]):
                print(f"Warning: Skipping invalid LRC entry: {entry}")
                continue

            start_time_str = format_time_lrc(entry["start"])
            text = entry["text"]

            # LRC usually expects a single line of lyrics per timestamp.
            # If text has newlines, we might take the first line or split them.
            # For simplicity, let's take the first line.
            first_line = text.split('\n')[0].strip()

            if first_line: # Only add if there's text
                lrc_content.append(f"[{start_time_str}]{first_line}")

        return "\n".join(lrc_content)