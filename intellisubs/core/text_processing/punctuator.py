# Punctuation Restoration Utilities

import logging
 
class Punctuator:
    def __init__(self, language: str = "ja", logger: logging.Logger = None):
        """
        Initializes the Punctuator.
        
        Args:
            language (str): Language code (e.g., "ja", "zh").
            logger (logging.Logger, optional): Logger instance.
        """
        self.logger = logger if logger else logging.getLogger(self.__class__.__name__)
        self.language = "ja" # Default, will be set by set_language
        self._period = "。"
        self._question_mark = "？"
        self._comma = "、" # Default Japanese comma
        self._ja_question_particles = ("か", "の")
        # Expanded list for Chinese question particles. Note: some can be ambiguous.
        self._zh_question_particles = ("吗", "呢", "么", "吧", "啊", "嘛", "不") # "不" for A-not-A questions like "是不是"

        self.set_language(language) # Set initial language and its specific punctuation
        self.logger.info(f"Punctuator initialized. Active language: {self.language}")

    def set_language(self, lang_code: str):
        """Sets the active language for punctuation."""
        self.language = lang_code.lower()
        if self.language == "zh":
            self._period = "。"
            self._question_mark = "？"
            self._comma = "，" # Chinese comma
            # Chinese question particles are checked differently, more contextually.
            # For simplicity, we might rely on sentence structure or specific end words.
        elif self.language == "ja":
            self._period = "。"
            self._question_mark = "？"
            self._comma = "、" # Japanese comma
        else:
            self.logger.warning(f"Unsupported language for Punctuator: '{self.language}'. Using default (Japanese-like) punctuation marks.")
            # Keep Japanese defaults if language is unknown
            self._period = "。"
            self._question_mark = "？"
            self._comma = "、"
        self.logger.info(f"Punctuator language set to: '{self.language}'. Period: '{self._period}', QMark: '{self._question_mark}', Comma: '{self._comma}'")

    def add_punctuation(self, text_segments: list) -> list:
        """
        Adds basic punctuation to a list of text segments based on simple heuristics
        and the currently set language.
        Focuses on adding period and question mark at segment ends.

        Args:
            text_segments (list): List of segment dicts.
        Returns:
            list: List of segment dicts with punctuation added.
        """
        self.logger.info(f"正在为 {len(text_segments)} 个片段添加标点符号 (语言: '{self.language}')。")
        punctuated_segments = []

        for i, seg in enumerate(text_segments):
            text = seg.get("text", "")
            if not text.strip(): # Skip empty segments
                punctuated_segments.append(seg)
                continue

            # Ensure text is clean before processing
            current_text = text.strip()
            
            # Remove existing ending punctuation (generic for common ones) to avoid duplicates
            # Consider language-specific "!" variants if needed.
            if current_text.endswith((self._period, self._question_mark, "!", "！")):
                current_text = current_text[:-1].strip() # Strip again after removing

            is_last_segment = (i == len(text_segments) - 1)
            significant_pause_after = False
            if not is_last_segment and text_segments[i+1].get("start") is not None and seg.get("end") is not None:
                if text_segments[i+1]["start"] - seg["end"] > 0.7: # Configurable threshold
                    significant_pause_after = True

            # Add punctuation based on context and language
            if is_last_segment or significant_pause_after:
                punctuated = False
                if self.language == "ja":
                    if any(current_text.endswith(p) for p in self._ja_question_particles):
                        current_text += self._question_mark
                        punctuated = True
                elif self.language == "zh":
                    # Check for standard question particles
                    if any(current_text.endswith(p) for p in self._zh_question_particles if p != "不"):
                        current_text += self._question_mark
                        punctuated = True
                    # Check for A-not-A pattern ending with "不" (e.g., "是不是", "好不好")
                    # This is a simple check, a more robust one would need more context.
                    elif current_text.endswith("不") and len(current_text) > 1 and current_text[-2] == current_text[0] : # e.g. X不X is too simple, check for common patterns
                        # A more robust check for A-not-A might be too complex here.
                        # Let's refine _zh_question_particles or rely on LLM for complex cases.
                        # For now, if ends with "不" and is a common phrase like "好不好", "是不是"
                        common_a_not_a_starters = ["是不", "可不", "能不", "会不会", "行不", "好不"] # "是不是" -> "是不"
                        if any(current_text.endswith(starter + "不") for starter in common_a_not_a_starters):
                             current_text += self._question_mark
                             punctuated = True
                        elif len(current_text) >= 2 and current_text[-2] != ' ': # Basic "X不" can sometimes be questions
                             # This is still too broad. Let's stick to the particle list for now.
                             pass


                # Add other language-specific question heuristics here if needed
                
                if not punctuated: # If not already ended with a question mark by lang-specific rules
                    # Avoid adding period if text is already somehow ending with one (e.g. from ASR)
                    if not current_text.endswith(self._period) and not current_text.endswith(self._question_mark):
                         current_text += self._period
            
            # Basic comma insertion can be added here, specific to self.language
            # e.g., if self.language == "zh": current_text = self._add_chinese_commas(current_text)
            # For now, focusing on sentence-ending punctuation.

            punctuated_segments.append({"text": current_text, "start": seg.get("start"), "end": seg.get("end")})

        self.logger.info(f"标点符号添加完成 ({self.language})，结果包含 {len(punctuated_segments)} 个片段。")
        return punctuated_segments