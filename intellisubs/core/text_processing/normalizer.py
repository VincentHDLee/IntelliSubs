# ASR Result Normalization Utilities

class ASRNormalizer:
    def __init__(self, custom_dictionary_path: str = None):
        """
        Initializes the ASRNormalizer.

        Args:
            custom_dictionary_path (str, optional): Path to a custom dictionary file.
                                                     Format could be CSV: "original_phrase,corrected_phrase"
        """
        self.custom_rules = {}
        if custom_dictionary_path:
            self.load_custom_dictionary(custom_dictionary_path)
        print(f"ASRNormalizer initialized. Custom rules loaded: {len(self.custom_rules)}") # Placeholder

    def load_custom_dictionary(self, file_path: str):
        """
        Loads custom replacement rules from a file.
        Example CSV line: "AIアシスタント,AIアシスタント" (no change if just for recognition)
                         "うぃすぱー,Whisper"
        """
        # Placeholder for actual file reading and parsing
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#') or ',' not in line:
                        continue
                    original, corrected = line.split(',', 1)
                    self.custom_rules[original.strip()] = corrected.strip()
            print(f"Loaded {len(self.custom_rules)} rules from {file_path}")
        except FileNotFoundError:
            print(f"Warning: Custom dictionary file not found: {file_path}")
        except Exception as e:
            print(f"Error loading custom dictionary {file_path}: {e}")


    def normalize_text_segments(self, segments: list) -> list:
        """
        Normalizes a list of ASR text segments.
        - Merges overly fragmented segments.
        - Applies custom dictionary replacements.
        - Removes common ASR errors or disfluencies (basic).

        Args:
            segments (list): List of segment dicts (e.g., [{'text': '...', 'start': ..., 'end': ...}, ...])

        Returns:
            list: List of normalized segment dicts.
        """
        print(f"Normalizing {len(segments)} text segments...") # Placeholder
        normalized_segments = []
        # Placeholder logic
        for i, seg in enumerate(segments):
            text = seg.get("text", "")

            # Apply custom rules
            for original, corrected in self.custom_rules.items():
                text = text.replace(original, corrected)

            # Basic disfluency removal (example)
            text = text.replace("えーと", "").replace("あのー", "").strip()
            text = " ".join(text.split()) # Normalize whitespace

            if text: # Only add if text is not empty after normalization
                normalized_segments.append({"text": text, "start": seg.get("start"), "end": seg.get("end")})

        # Placeholder for merging logic (more complex)
        # This would involve looking at timings and text length
        if len(normalized_segments) > 1:
            print("Segment merging logic would be applied here.")

        print(f"Normalization resulted in {len(normalized_segments)} segments.") # Placeholder
        return normalized_segments if normalized_segments else segments # Return original if all became empty