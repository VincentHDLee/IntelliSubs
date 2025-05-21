# LLM Text Enhancement Utilities

from openai import OpenAI
import os
import logging

class LLMEnhancer:
    def __init__(self, api_key: str = None, model_name: str = "gpt-3.5-turbo", language: str = "ja", logger: logging.Logger = None):
        """
        Initializes the LLMEnhancer.

        Args:
            api_key (str, optional): The API key for the LLM service.
                                     If None, it tries to read from an environment variable (OPENAI_API_KEY).
            model_name (str): The name of the LLM model to use.
            language (str): Language of the text to be enhanced (e.g., "ja").
            logger (logging.Logger, optional): Logger instance.
        """
        self.logger = logger if logger else logging.getLogger(self.__class__.__name__)
        self.model_name = model_name
        self.language = language
        self.client = None
        self.api_key_provided = False

        if api_key:
            self.client = OpenAI(api_key=api_key)
            self.api_key_provided = True
            self.logger.info("LLMEnhancer: API key provided directly.")
        elif os.getenv("OPENAI_API_KEY"):
            self.client = OpenAI() # Reads from env var OPENAI_API_KEY
            self.api_key_provided = True
            self.logger.info("LLMEnhancer: API key loaded from environment variable.")
        else:
            self.logger.warning("LLMEnhancer initialized without API key. Enhancement will be skipped.")

        self.logger.info(f"LLMEnhancer initialized for model: {model_name}, lang: {language}. API Client available: {self.client is not None}")

    def enhance_text_segments(self, text_segments: list) -> list:
        """
        Enhances text segments using an LLM.

        This could involve:
        - More sophisticated punctuation.
        - Grammar correction.
        - Text polishing (smoothing, rephrasing for clarity).
        - Adjusting formality (e.g., Japanese Keigo), if prompted.

        Args:
            text_segments (list): List of segment dicts (e.g., [{'text': '...', 'start': ..., 'end': ...}, ...])
                                  Assumes text is somewhat clean but could be improved.

        Returns:
            list: List of segment dicts with LLM-enhanced text.
        """
        if not self.client:
            self.logger.warning("LLM enhancement skipped: API client not available.")
            return text_segments

        self.logger.info(f"Using LLM ({self.model_name}) 增强 {len(text_segments)} 个文本片段。")
        enhanced_segments = []

        system_prompt_ja = "あなたは日本語のビデオ字幕編集の専門家です。提供されたテキストを自然さ、正しい句読点、明瞭さに重点を置いて洗練してください。"
        user_prompt_template_ja = "以下の日本語のテキストを洗練してください。テキスト：「{text}」"

        for seg in text_segments:
            original_text = seg.get("text", "")
            if not original_text.strip():
                enhanced_segments.append(seg)
                continue

            try:
                # Construct prompt based on language
                if self.language == "ja":
                    prompt = user_prompt_template_ja.format(text=original_text)
                    messages = [
                        {"role": "system", "content": system_prompt_ja},
                        {"role": "user", "content": prompt}
                    ]
                else:
                    # Fallback or extend with other languages
                    prompt = f"Please refine the following text for a video subtitle. Focus on naturalness, correct punctuation, and clarity. Text: \"{original_text}\""
                    messages = [
                        {"role": "system", "content": "You are an expert in subtitle editing."},
                        {"role": "user", "content": prompt}
                    ]

                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.7, # Adjust temperature for creativity/consistency
                    max_tokens=200 # Limit response length
                )
                enhanced_text = response.choices[0].message.content.strip()
                self.logger.debug(f"原始: '{original_text}' -> 增强: '{enhanced_text}'")
                enhanced_segments.append({"text": enhanced_text, "start": seg.get("start"), "end": seg.get("end")})

            except Exception as e:
                self.logger.error(f"LLM增强片段失败 '{original_text[:30]}...': {e}", exc_info=True)
                enhanced_segments.append(seg) # Fallback to original segment on error

        self.logger.info(f"LLM增强完成，生成 {len(enhanced_segments)} 个片段。")
        return enhanced_segments