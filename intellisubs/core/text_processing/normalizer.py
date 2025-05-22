# ASR Result Normalization Utilities

import logging
import os
import csv
 
class ASRNormalizer:
    def __init__(self, custom_dictionary_path: str = None, logger: logging.Logger = None):
        """
        Initializes the ASRNormalizer.
        
        Args:
            custom_dictionary_path (str, optional): Path to a custom dictionary file (CSV).
            logger (logging.Logger, optional): Logger instance.
        """
        self.logger = logger if logger else logging.getLogger(self.__class__.__name__)
        self.custom_rules = {}
        self.current_dictionary_path = None # Store the path of the loaded dictionary
        self.common_disfluencies = ["えーと", "あのー", "そのー", "ええと", "はい", "うん", "ふん"] # Common Japanese disfluencies
        
        if custom_dictionary_path:
            self.set_custom_dictionary_path(custom_dictionary_path)
        else:
            self.logger.info("ASRNormalizer initialized without a custom dictionary.")

    def set_custom_dictionary_path(self, new_path: str):
        """
        Sets a new custom dictionary file and loads it.
        If the new path is the same as the currently loaded one, it does nothing.
        """
        if new_path == self.current_dictionary_path and self.custom_rules: # Already loaded and has rules
            self.logger.info(f"Custom dictionary '{new_path}' is already loaded. Skipping reload.")
            return

        self.logger.info(f"Attempting to load custom dictionary from: {new_path}")
        self.custom_rules.clear() # Clear any existing rules
        self.current_dictionary_path = new_path # Update path before loading
        if new_path and os.path.exists(new_path): # Ensure path is not empty and exists
            self._load_dictionary_from_file(new_path) # Changed to private method
        elif new_path: # Path provided but does not exist
            self.logger.warning(f"Custom dictionary file not found at '{new_path}'. No custom rules will be loaded.")
            # self.current_dictionary_path will remain as new_path, even if not found
        else: # Path is empty or None
            self.logger.info("No custom dictionary path provided. No custom rules will be loaded.")
            self.current_dictionary_path = None # Explicitly set to None

        self.logger.info(f"ASRNormalizer: Custom rules active: {len(self.custom_rules)} (from: {self.current_dictionary_path if self.current_dictionary_path else 'None'})")


    def _load_dictionary_from_file(self, file_path: str): # Renamed from load_custom_dictionary
        """
        Loads custom replacement rules from a CSV file.
        Each line should be: "original_phrase,corrected_phrase"
        Example: "うぃすぱー,Whisper"
        """
        if not os.path.exists(file_path):
            self.logger.warning(f"自定义词典文件未找到: {file_path}。将不加载任何自定义规则。")
            return

        try:
            with open(file_path, 'r', encoding='utf-8', newline='') as f:
                reader = csv.reader(f)
                for i, row in enumerate(reader):
                    if not row or row[0].strip().startswith('#'): # Skip empty rows and comments
                        continue
                    if len(row) == 2:
                        original = row[0].strip()
                        corrected = row[1].strip()
                        self.custom_rules[original] = corrected
                    else:
                        self.logger.warning(f"自定义词典 '{file_path}' 中格式错误的行 (行 {i+1}): {row}。跳过。")
            self.logger.info(f"已从 '{file_path}' 加载 {len(self.custom_rules)} 条自定义规则。")
        # Removed FileNotFoundError as the new structure should handle it before calling this.
        except Exception as e:
            self.logger.error(f"加载自定义词典 '{file_path}' 时出错: {e}", exc_info=True)
            self.custom_rules.clear() # Clear rules if loading failed to prevent partial state
            # self.current_dictionary_path remains to indicate an attempt was made for this path


    def normalize_text_segments(self, segments: list) -> list:
        """
        Normalizes a list of ASR text segments.
        - Applies custom dictionary replacements.
        - Removes common ASR errors or disfluencies.
        - Merges overly fragmented segments (based on timing).

        Args:
            segments (list): List of segment dicts (e.g., [{'text': '...', 'start': ..., 'end': ...}, ...])

        Returns:
            list: List of normalized and potentially merged segment dicts.
        """
        self.logger.info(f"开始规范化 {len(segments)} 个文本片段。")
        processed_segments = []

        for seg in segments:
            text = seg.get("text", "")
            start = seg.get("start")
            end = seg.get("end")

            # 1. Apply custom dictionary rules
            for original, corrected in self.custom_rules.items():
                text = text.replace(original, corrected)
            
            # 2. Remove common ASR errors or disfluencies
            for disfluency in self.common_disfluencies:
                text = text.replace(disfluency, "")
            
            text = text.strip() # Remove leading/trailing whitespace after replacements

            # Normalize multiple spaces to single space
            text = " ".join(text.split())

            if text: # Only include if text is not empty
                processed_segments.append({"text": text, "start": start, "end": end})

        # 3. Merge overly fragmented segments (e.g., very short pauses)
        # Threshold for merging: ASR_MERGE_TIME_THRESHOLD (e.g., 0.3-0.5 seconds)
        # ASR_MERGE_CHAR_LIMIT (e.g., 5-10 chars for very short segments)
        merged_segments = []
        if processed_segments:
            current_segment = processed_segments[0].copy()
            for i in range(1, len(processed_segments)):
                next_segment = processed_segments[i]
                
                # Check for short pause and short text (configurable thresholds)
                # These thresholds should ideally come from config_manager or be constant.
                # For now, hardcoding as per DEVELOPMENT.md suggestion (0.3-0.5s pause, < 10 chars)
                if (next_segment["start"] - current_segment["end"] <= 0.4) and \
                   (len(next_segment["text"]) <= 10): # Example heuristic
                    current_segment["text"] += next_segment["text"]
                    current_segment["end"] = next_segment["end"]
                    self.logger.debug(f"合并片段: '{current_segment['text']}'")
                else:
                    merged_segments.append(current_segment)
                    current_segment = next_segment.copy()
            merged_segments.append(current_segment) # Add the last segment

        self.logger.info(f"规范化完成。从 {len(segments)} 个片段处理到 {len(merged_segments)} 个片段。")
        return merged_segments if merged_segments else processed_segments # Return processed if merging resulted in empty list (unlikely)