# Punctuation Restoration Utilities

import logging
 
class Punctuator:
    def __init__(self, language: str = "ja", logger: logging.Logger = None):
        """
        Initializes the Punctuator.
        
        Args:
            language (str): Language code (e.g., "ja" for Japanese).
                            This might influence punctuation rules.
            logger (logging.Logger, optional): Logger instance.
        """
        self.logger = logger if logger else logging.getLogger(self.__class__.__name__)
        self.language = language
        self.logger.info(f"Punctuator initialized for language: {language}")

    def add_punctuation(self, text_segments: list) -> list:
        """
        Adds basic Japanese punctuation to a list of text segments based on simple heuristics.
        This focuses on adding "。" (period) and "？" (question mark) at segment ends,
        and basic "、" (comma) insertion.

        Args:
            text_segments (list): List of segment dicts
                                  (e.g., [{'text': '...', 'start': ..., 'end': ...}, ...])
                                  It's assumed text here is already normalized.

        Returns:
            list: List of segment dicts with punctuation added to the text.
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
            
            # Remove existing ending punctuation to avoid duplicates
            if current_text.endswith(("。", "！", "？")):
                current_text = current_text[:-1]

            # Heuristic for adding Japanese period (。) or question mark (？)
            # Check for significant pause before next segment or if it's the last segment
            is_last_segment = (i == len(text_segments) - 1)
            significant_pause_after = False
            if not is_last_segment and text_segments[i+1].get("start") is not None and seg.get("end") is not None:
                # Use a configurable threshold, e.g., 0.7 seconds as suggested in DEVELOPMENT.md
                if text_segments[i+1]["start"] - seg["end"] > 0.7:
                    significant_pause_after = True

            # Add punctuation based on context
            if is_last_segment or significant_pause_after:
                if current_text.endswith("か") or current_text.endswith("の"): # Common Japanese question particles
                    current_text += "？"
                elif not current_text.endswith("。"): # Avoid double periods if already present
                    current_text += "。"
            
            # Basic comma insertion (very naive, can be improved with more sophisticated NLP)
            # This is a simple example. A real implementation might use a model or more rules.
            # Example: after particles like 「は」「が」「に」「を」「で」 if followed by a pause/new clause
            # For simplicity, let's keep it simple for now, focusing on sentence-ending punct.

            punctuated_segments.append({"text": current_text, "start": seg.get("start"), "end": seg.get("end")})

        self.logger.info(f"标点符号添加完成，结果包含 {len(punctuated_segments)} 个片段。")
        return punctuated_segments