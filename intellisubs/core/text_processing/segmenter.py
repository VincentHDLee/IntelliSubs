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
        
        self._strong_break_punctuations = {"。", "！", "？"}
        self._line_internal_break_punctuations = {"。", "、", "！", "？", "，"}
        
        self._ja_particle_heuristics = ("は", "が", "を", "に", "で", "と", "も", "へ", "から", "まで", "より")
        self._zh_heuristic_break_words = (
            "的话", "的时候", "之后", "之前", "然后", "但是", "不过", "而且", "所以", "因此",
            "于是", "另外", "例如", "比如", "方面", "来说", "一般", "目前", "现在"
        ) # Common points where a sentence might naturally break or pause in Chinese.

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
        lines = []
        original_text_remaining = text.strip()
        max_lines = 2  # Max lines per subtitle entry

        while original_text_remaining and len(lines) < max_lines:
            if len(original_text_remaining) <= self.max_chars_per_line:
                lines.append(original_text_remaining)
                break # All remaining text fits in one line

            possible_break_idx = -1
            # Determine the search range: from max_chars_per_line down to a reasonable minimum (e.g., 40% of max_chars)
            # Ensure search_end_idx is not negative if max_chars_per_line is small.
            search_end_idx = max(0, int(self.max_chars_per_line * 0.4) -1)


            # 1. Try to break at preferred punctuations first
            for i in range(min(len(original_text_remaining) - 1, self.max_chars_per_line), search_end_idx, -1):
                if original_text_remaining[i] in self._line_internal_break_punctuations:
                    # Check if this punctuation is a good breaking point
                    # (e.g., not immediately followed by another strong punctuation that should stick together)
                    if (i + 1 < len(original_text_remaining) and \
                        original_text_remaining[i+1] not in self._strong_break_punctuations) or \
                       (i + 1 == len(original_text_remaining)): # It's the last char
                        possible_break_idx = i + 1  # Break after the punctuation
                        break
            
            # 2. If no punctuation break, try language-specific heuristics
            if possible_break_idx == -1:
                # Search text is the part of original_text_remaining that could form the current line
                # We look for heuristics within this potential line, preferably towards its end.
                current_line_candidate = original_text_remaining[:self.max_chars_per_line + 10] # Check a bit beyond max_chars

                if self.language == "ja":
                    for i in range(min(len(current_line_candidate) - 1, self.max_chars_per_line), search_end_idx, -1):
                        if current_line_candidate[i] in self._ja_particle_heuristics:
                            if (i + 1 < len(current_line_candidate) and \
                                current_line_candidate[i+1] not in self._line_internal_break_punctuations):
                                possible_break_idx = i + 1
                                break
                elif self.language == "zh":
                    for i in range(min(len(current_line_candidate) - 1, self.max_chars_per_line), search_end_idx, -1):
                        # Check if the substring ending at `i` is one of the heuristic words
                        for zh_word in self._zh_heuristic_break_words:
                            if current_line_candidate[:i+1].endswith(zh_word):
                                # Ensure it's a good break (e.g., not immediately followed by punctuation)
                                if (i + 1 < len(current_line_candidate) and \
                                    current_line_candidate[i+1] not in self._line_internal_break_punctuations) or \
                                   (i + 1 == len(current_line_candidate)):
                                    possible_break_idx = i + 1
                                    break
                        if possible_break_idx != -1:
                            break
            
            # 3. Determine the line and update remaining text
            if possible_break_idx != -1:
                line_to_add = original_text_remaining[:possible_break_idx].strip()
                original_text_remaining = original_text_remaining[possible_break_idx:].strip()
            else:  # Fallback to hard break if no better option
                line_to_add = original_text_remaining[:self.max_chars_per_line].strip()
                original_text_remaining = original_text_remaining[self.max_chars_per_line:].strip()
            
            lines.append(line_to_add)

        # If there's still text remaining after filling max_lines, append it to the last line
        if original_text_remaining and lines: # Check if lines is not empty
            lines[-1] = (lines[-1] + (" " if self.language not in ["ja", "zh"] else "") + original_text_remaining).strip()

        # Post-processing: if the second line is very short, try to merge it back
        if len(lines) == 2 and len(lines[1]) < self.max_chars_per_line * 0.3:
            if (len(lines[0]) + len(lines[1])) < (self.max_chars_per_line * 1.5):
                first_line_ends_with_strong_punc = any(lines[0].endswith(p) for p in self._strong_break_punctuations)
                if not first_line_ends_with_strong_punc:
                    return (lines[0] + (" " if self.language not in ["ja", "zh"] else "") + lines[1]).strip()

        return "\n".join(lines)