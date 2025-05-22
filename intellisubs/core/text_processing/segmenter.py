# Subtitle Segmentation Utilities

import logging
 
class SubtitleSegmenter:
    def __init__(self, max_chars_per_line: int = 25, max_duration_sec: float = 7.0, language: str = "ja", logger: logging.Logger = None):
        """
        Initializes the SubtitleSegmenter.
        
        Args:
            max_chars_per_line (int): Approx. max characters per subtitle line.
            max_duration_sec (float): Max duration for a single subtitle entry.
            language (str): Language code (e.g., "ja", "zh").
            logger (logging.Logger, optional): Logger instance.
        """
        self.logger = logger if logger else logging.getLogger(self.__class__.__name__)
        self.max_chars_per_line = max_chars_per_line
        self.max_duration_sec = max_duration_sec
        
        self.language = "ja" # Default, will be updated by set_language
        self._comma = "、"
        self._period = "。"
        self._question_mark = "？"
        self._exclamation_mark = "！"
        # Punctuations that can end a sentence or a clause suitable for a subtitle break
        self._strong_break_punctuations = {"。", "！", "？"}
        # Punctuations that can be used for line breaking within a subtitle entry
        self._line_internal_break_punctuations = {"。", "、", "！", "？", "，"} # Include Chinese comma for _format_lines
        self._ja_particle_heuristics = ("は", "が", "を", "に", "で", "と", "も", "へ", "から", "まで", "より")

        self.set_language(language) # Set initial language
        self.logger.info(f"SubtitleSegmenter initialized. Active lang: {self.language}, max_chars={self.max_chars_per_line}, max_duration={self.max_duration_sec}s")

    def set_language(self, lang_code: str):
        """Sets the active language for segmentation rules."""
        self.language = lang_code.lower()
        if self.language == "zh":
            self._comma = "，"
            self._period = "。"
            self._question_mark = "？"
            self._exclamation_mark = "！"
            self._strong_break_punctuations = {"。", "！", "？"}
            self._line_internal_break_punctuations = {"。", "，", "！", "？"}
        elif self.language == "ja":
            self._comma = "、"
            self._period = "。"
            self._question_mark = "？"
            self._exclamation_mark = "！"
            self._strong_break_punctuations = {"。", "！", "？"}
            self._line_internal_break_punctuations = {"。", "、", "！", "？"}
        else:
            self.logger.warning(f"Unsupported language for SubtitleSegmenter: '{self.language}'. Using default (Japanese-like) punctuation sets.")
            self._comma = "、"
            self._period = "。"
            self._question_mark = "？"
            self._exclamation_mark = "！"
            self._strong_break_punctuations = {"。", "！", "？"}
            self._line_internal_break_punctuations = {"。", "、", "！", "？"}
        self.logger.info(f"SubtitleSegmenter language set to: '{self.language}'. Comma: '{self._comma}', StrongPunc: {self._strong_break_punctuations}")

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

                # 3. Check for strong punctuation breaks (using language-specific strong punctuations)
                if any(current_subtitle_text.endswith(punc) for punc in self._strong_break_punctuations) and \
                   (start_time - current_subtitle_end > 0.5): # Significant pause
                   should_break = True
                   self.logger.debug(f"因强标点 ({current_subtitle_text[-1]}) 和停顿而断句。")
                
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
                    # Consider adding a space if merging separate "words" without natural break.
                    # For Ja/Zh, usually no space needed unless forced merge of very distinct phrases.
                    if current_subtitle_text and \
                       not any(current_subtitle_text.endswith(punc) for punc in self._strong_break_punctuations) and \
                       not current_subtitle_text.endswith(self._comma):
                        # current_subtitle_text += "" # No space generally needed for Ja/Zh text merge
                        pass
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
        and language-specific rules (prioritizing punctuation breaks).
        Limits to a configurable number of lines (e.g., 2) for readability.
        """
        # Use self._line_internal_break_punctuations which includes the correct comma for the language
        punctuations_for_internal_break = self._line_internal_break_punctuations

        lines = []
        current_line_text = ""
        original_text_remaining = text.strip()

        max_lines = 2 # Configurable: max lines per subtitle entry

        while original_text_remaining and len(lines) < max_lines:
            if len(original_text_remaining) <= self.max_chars_per_line:
                lines.append(original_text_remaining)
                original_text_remaining = ""
                break

            # Try to find a break point within max_chars_per_line
            possible_break_idx = -1
            # Search backwards from max_chars_per_line
            for i in range(min(len(original_text_remaining) -1, self.max_chars_per_line), 0, -1):
                if original_text_remaining[i] in punctuations_for_internal_break:
                    # Ensure it's a good break (e.g., not breaking just before another punctuation if it's the end)
                    # Or if the punctuation is a comma, and the next char is not also a strong punctuation.
                    if i + 1 < len(original_text_remaining) and original_text_remaining[i+1] not in self._strong_break_punctuations:
                         possible_break_idx = i + 1 # Break after the punctuation
                         break
                    elif i + 1 == len(original_text_remaining): # Punctuation is last char of remaining
                         possible_break_idx = i + 1
                         break
                # Japanese particle heuristic (only if language is Japanese)
                if self.language == "ja" and original_text_remaining[i] in self._ja_particle_heuristics:
                    if i + 1 < len(original_text_remaining) and \
                       original_text_remaining[i+1] not in punctuations_for_internal_break: # Avoid breaking "particle。"
                        possible_break_idx = i + 1
                        break
            
            if possible_break_idx != -1:
                current_line_text = original_text_remaining[:possible_break_idx].strip()
                original_text_remaining = original_text_remaining[possible_break_idx:].strip()
            else: # No good punctuation/particle break found, hard break at max_chars_per_line (or space if available)
                # This part would need refinement for languages that use spaces.
                # For Ja/Zh, a hard character limit break is common if no punc.
                current_line_text = original_text_remaining[:self.max_chars_per_line].strip()
                original_text_remaining = original_text_remaining[self.max_chars_per_line:].strip()

            lines.append(current_line_text)

        if original_text_remaining and len(lines) == max_lines: # If there's still text but we hit max lines
            lines[-1] += original_text_remaining # Append remaining to the last line

        # Final check: if the second line is very short, try to merge it back if first is not too long
        if len(lines) == 2 and len(lines[1]) < self.max_chars_per_line * 0.3: # e.g. less than 30% of max
            if (len(lines[0]) + len(lines[1])) < (self.max_chars_per_line * 1.5): # Allow some overflow if merging
                first_line_ends_with_strong_punc = any(lines[0].endswith(p) for p in self._strong_break_punctuations)
                if not first_line_ends_with_strong_punc: # Don't merge if first line clearly ends a sentence
                    merged_text = lines[0] + (" " if self.language not in ["ja", "zh"] else "") + lines[1]
                    return merged_text.strip()
        
        return "\n".join(lines)