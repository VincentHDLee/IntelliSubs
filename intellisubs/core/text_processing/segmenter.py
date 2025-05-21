# Subtitle Segmentation Utilities

import logging
 
class SubtitleSegmenter:
    def __init__(self, max_chars_per_line: int = 25, max_duration_sec: float = 7.0, language: str = "ja", logger: logging.Logger = None):
        """
        Initializes the SubtitleSegmenter.
        
        Args:
            max_chars_per_line (int): Maximum number of characters (approx) per subtitle line.
                                      For Japanese, this usually refers to full-width characters.
            max_duration_sec (float): Maximum duration for a single subtitle entry.
            language (str): Language code, e.g., "ja".
            logger (logging.Logger, optional): Logger instance.
        """
        self.logger = logger if logger else logging.getLogger(self.__class__.__name__)
        self.max_chars_per_line = max_chars_per_line
        self.max_duration_sec = max_duration_sec
        self.language = language
        self.logger.info(f"SubtitleSegmenter initialized: max_chars={max_chars_per_line}, max_duration={max_duration_sec}s, lang={language}")

    def segment_into_subtitle_lines(self, punctuated_text_segments: list) -> list:
        """
        Segments ASR text (already punctuated) into appropriate subtitle lines.
        Considers line length, duration, and natural break points (punctuation).

        Args:
            punctuated_text_segments (list): List of segment dicts from Punctuator
                                             (e.g., [{'text': 'こんにちは。世界！', 'start': 0.5, 'end': 2.8}, ...])

        Returns:
            list: List of subtitle entry dicts, where each entry represents a complete subtitle.
                  Each dict: {'text': '行1\n行2', 'start': 0.5, 'end': 2.8}
        """
        self.logger.info(f"正在将 {len(punctuated_text_segments)} 个已加标点的ASR片段分段为字幕行。")
        subtitle_entries = []
        
        current_subtitle_text = ""
        current_subtitle_start = None
        current_subtitle_end = None

        for i, seg in enumerate(punctuated_text_segments):
            text = seg.get("text", "")
            start_time = seg.get("start")
            end_time = seg.get("end")

            if not text.strip() or start_time is None or end_time is None:
                continue

            if current_subtitle_text == "": # First segment of a new subtitle entry
                current_subtitle_text = text
                current_subtitle_start = start_time
                current_subtitle_end = end_time
            else:
                # Check for natural break points and length constraints
                should_break = False

                # 1. Check duration
                if (end_time - current_subtitle_start) > self.max_duration_sec:
                    should_break = True
                    self.logger.debug(f"因时长超限而断句: {end_time - current_subtitle_start:.2f}s > {self.max_duration_sec}s")

                # 2. Check character limit (approximate for Japanese full-width chars)
                if len(current_subtitle_text.replace('\n', '')) >= self.max_chars_per_line:
                    should_break = True
                    self.logger.debug(f"因字符数超限而断句: {len(current_subtitle_text)} > {self.max_chars_per_line}")

                # 3. Check for strong punctuation breaks (if not already handled by previous segmentation logic)
                # If current segment ends with a strong punctuation and is followed by a pause
                if current_subtitle_text.endswith(("。", "！", "？")) and \
                   (start_time - current_subtitle_end > 0.5): # Significant pause
                   should_break = True
                   self.logger.debug(f"因强标点和停顿而断句。")
                
                # If we should break, finalize the current subtitle and start a new one
                if should_break:
                    # Finalize current subtitle
                    finalized_text = self._format_lines(current_subtitle_text)
                    subtitle_entries.append({
                        "text": finalized_text,
                        "start": current_subtitle_start,
                        "end": current_subtitle_end
                    })
                    self.logger.debug(f"生成字幕: '{finalized_text}' ({current_subtitle_start:.2f}-{current_subtitle_end:.2f})")

                    # Start new subtitle with the current segment
                    current_subtitle_text = text
                    current_subtitle_start = start_time
                    current_subtitle_end = end_time
                else:
                    # Append current segment's text to the existing subtitle
                    # Consider adding a space if merging separate "words" without natural break
                    if current_subtitle_text and not current_subtitle_text.endswith(tuple("、。？！")): # If previous line didn't end with punctuation
                        current_subtitle_text += "" # Japanese usually doesn't need space, but if words are distinct
                    current_subtitle_text += text
                    current_subtitle_end = end_time # Extend end time

        # Add the last accumulated subtitle entry if any
        if current_subtitle_text:
            finalized_text = self._format_lines(current_subtitle_text)
            subtitle_entries.append({
                "text": finalized_text,
                "start": current_subtitle_start,
                "end": current_subtitle_end
            })
            self.logger.debug(f"生成最终字幕: '{finalized_text}' ({current_subtitle_start:.2f}-{current_subtitle_end:.2f})")

        self.logger.info(f"字幕分段完成。生成 {len(subtitle_entries)} 个字幕条目。")
        return subtitle_entries

    def _format_lines(self, text: str) -> str:
        """
        Helper to break a single text string into multiple lines based on max_chars_per_line
        and Japanese-specific rules (prioritizing punctuation breaks).
        Limits to 2 lines for readability.
        """
        lines = []
        current_line = ""
        for char in text:
            current_line += char
            # Prioritize breaking at full-width punctuation
            if char in ("。", "、", "！", "？") and len(current_line) > (self.max_chars_per_line * 0.7):
                lines.append(current_line.strip())
                current_line = ""
            elif len(current_line) >= self.max_chars_per_line:
                # If line is too long without punctuation, try to find a natural break (e.g., after hiragana/katakana that marks a particle)
                # This is a very basic heuristic. More advanced would use morphological analysis.
                break_found = False
                for j in range(len(current_line) - 1, int(self.max_chars_per_line * 0.5) - 1, -1): # Search backwards from end
                    # Simple check: break after a character that is typically followed by a space/break in Japanese
                    # This is highly simplified and might not be accurate for all cases
                    if current_line[j] in ("は", "が", "を", "に", "で", "と", "も", "へ", "から", "まで", "より") and \
                       j < len(current_line) - 1: # Avoid breaking just before punctuation attached to particle
                        lines.append(current_line[:j+1].strip())
                        current_line = current_line[j+1:].strip()
                        break_found = True
                        break
                
                if not break_found: # If no natural break found, just hard break
                    lines.append(current_line.strip())
                    current_line = ""
        
        if current_line:
            lines.append(current_line.strip())
        
        # Limit to 2 lines for a single subtitle entry, join with newline
        return "\n".join(lines[:2])