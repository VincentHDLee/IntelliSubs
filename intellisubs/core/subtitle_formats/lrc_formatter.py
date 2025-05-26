# LRC Subtitle Formatter
from .base_formatter import BaseSubtitleFormatter
import math # math might still be used if SubRipTime doesn't provide everything directly
import pysrt

# Module-level format_time_lrc is no longer needed.

class LRCFormatter(BaseSubtitleFormatter):
    def __init__(self, logger=None):
        super().__init__(logger)
        self.logger.info("LRCFormatter initialized.")

    def format_subtitles(self, subtitle_entries: list) -> str:
        """
        Formats subtitle entries into LRC format.
        LRC typically has one line of text per timestamp. If an entry has multiple
        lines (e.g., "Line1\nLine2"), they might be output as separate LRC lines
        with the same start timestamp, or the formatter might choose to only use
        the first line. For this basic version, we'll take the first line if multiple.

        Args:
            subtitle_entries (list): List of pysrt.SubRipItem objects.

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
            if not isinstance(entry, pysrt.SubRipItem):
                self.logger.warning(f"LRCFormatter: Entry is not a SubRipItem: {type(entry)}. Skipping.")
                continue

            # entry.start is a pysrt.SubRipTime object
            # LRC format: [mm:ss.xx] (xx is hundredths of a second)
            lrc_minutes = entry.start.minutes
            if hasattr(entry.start, 'hours') and entry.start.hours > 0:
                lrc_minutes += entry.start.hours * 60
            
            lrc_seconds = entry.start.seconds
            lrc_hundredths = entry.start.milliseconds // 10 # Convert milliseconds to hundredths

            start_time_str = f"{int(lrc_minutes):02d}:{int(lrc_seconds):02d}.{int(lrc_hundredths):02d}"
            text = entry.text

            # LRC usually expects a single line of lyrics per timestamp.
            # If text has newlines, we might take the first line or split them.
            # For simplicity, let's take the first line.
            first_line = text.split('\n')[0].strip()

            if first_line: # Only add if there's text
                lrc_content.append(f"[{start_time_str}]{first_line}")

        return "\n".join(lrc_content)