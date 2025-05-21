# LLM Text Enhancement Utilities

import httpx # For direct HTTP requests
import asyncio
import logging
import json # For parsing JSON response

class LLMEnhancer:
    def __init__(self, api_key: str, model_name: str = "gpt-3.5-turbo", base_url: str = None, language: str = "ja", logger: logging.Logger = None):
        """
        Initializes the LLMEnhancer for direct HTTP POST requests.

        Args:
            api_key (str): The API key for the LLM service.
            model_name (str): The name of the LLM model to use.
            base_url (str, optional): The base domain provided by the user (e.g., https://sucoiapi.com).
                                      The path /v1/chat/completions will be appended by this class.
            language (str): Language of the text to be enhanced (e.g., "ja").
            logger (logging.Logger, optional): Logger instance.
        """
        self.logger = logger if logger else logging.getLogger(self.__class__.__name__)
        self.model_name = model_name
        self.language = language
        self.api_key = api_key
        self.http_client = httpx.AsyncClient(timeout=30.0) # Standard timeout for HTTP requests
        self.api_key_provided = bool(api_key)
        
        self.base_domain_for_requests = "" 
        if isinstance(base_url, str) and base_url:
            # Caller (WorkflowManager) should have already aggressively cleaned the base_url.
            # We just ensure no trailing slash here for consistency before appending our path.
            self.base_domain_for_requests = base_url.rstrip('/')
            self.logger.info(f"LLMEnhancer: User-provided domain for LLM requests: '{self.base_domain_for_requests}'.")
        else:
            self.logger.warning("LLMEnhancer: Base URL (domain) not provided or invalid. LLM calls will likely fail if a custom domain is required.")

        if not self.api_key_provided:
            self.logger.warning("LLMEnhancer: API key not provided. Enhancement features will be unavailable.")

        self.logger.info(f"LLMEnhancer (direct HTTP mode) setup complete for model: {model_name}, lang: {language}. API Key Provided: {self.api_key_provided}, Target Domain: '{self.base_domain_for_requests}'")

    async def async_enhance_text_segments(self, text_segments: list) -> list:
        """
        Asynchronously enhances text segments using direct HTTP POST requests.
        """
        if not self.api_key_provided :
            self.logger.warning("LLM enhancement skipped: API key not provided.")
            return text_segments
        # Ensure base_domain_for_requests is set if we are attempting to use LLM
        if not self.base_domain_for_requests:
             self.logger.warning("LLM enhancement skipped: Base domain not provided for custom API.")
             return text_segments

        self.logger.info(f"Starting async LLM ({self.model_name}) enhancement for {len(text_segments)} text segments (direct HTTP).")
        
        tasks = []
        for seg_idx, seg in enumerate(text_segments):
            tasks.append(self._process_segment_async(seg, seg_idx))
        
        enhanced_segments_results = await asyncio.gather(*tasks, return_exceptions=True)

        final_enhanced_segments = []
        for i, result in enumerate(enhanced_segments_results):
            original_segment = text_segments[i]
            if isinstance(result, Exception):
                self.logger.error(f"Error processing segment {i} ('{original_segment.get('text', '')[:30]}...'): {result}", exc_info=True)
                final_enhanced_segments.append(original_segment) 
            elif result is None: 
                self.logger.error(f"Segment {i} processing returned None unexpectedly. Reverting to original.")
                final_enhanced_segments.append(original_segment)
            else:
                final_enhanced_segments.append(result)

        self.logger.info(f"Async LLM enhancement (direct HTTP) completed. Processed {len(final_enhanced_segments)} segments.")
        return final_enhanced_segments

    async def _process_segment_async(self, seg: dict, seg_idx: int) -> dict:
        """
        Asynchronously processes a single text segment by making a direct HTTP POST request
        to an OpenAI-compatible Chat Completions endpoint.
        The target URL is constructed from base_domain_for_requests + "/v1/chat/completions".
        """
        original_text = seg.get("text", "")
        if not original_text.strip():
            return seg # Return original segment if text is empty

        # This check is now at the beginning of async_enhance_text_segments
        # if not self.api_key_provided or not self.base_domain_for_requests:
        #     self.logger.warning(f"Segment {seg_idx}: Skipping LLM enhancement due to missing API key or base domain.")
        #     return {"text": original_text, "start": seg.get("start"), "end": seg.get("end")}
            
        target_url = f"{self.base_domain_for_requests}/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        if self.language == "ja":
            # Grok's suggested prompt - combining system instruction and original text more directly
            # and explicitly asking for non-empty result.
            system_prompt_content = (
                "あなたは日本語のビデオ字幕編集の専門家です。"
                "以下のテキストを自然で読みやすい日本語字幕に最適化し、句読点を適切に調整し、明瞭さを向上させてください。"
                "必ず結果を返し、空の応答を避けてください。\n"
                "例: 入力: 'こんにちは皆さん元気？' → 出力: 'こんにちは、皆さん。元気ですか？'"
            )
            # User content now just provides the text to be processed by the system prompt.
            user_prompt_content = f"テキスト：「{original_text}」"

        else: # Fallback for other languages
            system_prompt_content = (
                "You are an expert in subtitle editing. Optimize the following text for natural, readable subtitles, "
                "adjusting punctuation and improving clarity. Ensure a result is returned and avoid empty responses.\n"
                "Example: Input: 'hello everyone hows it going' -> Output: 'Hello, everyone. How's it going?'"
            )
            user_prompt_content = f"Text: \"{original_text}\""
        
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt_content},
                {"role": "user", "content": user_prompt_content} # User prompt provides the text within the context of system prompt
            ],
            "temperature": 0.3,  # Lowered for more deterministic output
            "max_tokens": max(300, int(len(original_text) * 3) + 100) # Increased max_tokens
        }
        
        self.logger.info(f"Segment {seg_idx}: Sending direct HTTP POST to {target_url} for LLM enhancement.")
        self.logger.debug(f"Segment {seg_idx}: Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")

        try:
            response = await self.http_client.post(target_url, json=payload, headers=headers)
            response.raise_for_status()
            response_data = response.json()
            self.logger.debug(f"Segment {seg_idx}: Full API response data: {json.dumps(response_data, ensure_ascii=False, indent=2)}")


            # Check for the presence of the expected structure
            choices = response_data.get('choices')
            if choices and isinstance(choices, list) and len(choices) > 0:
                first_choice = choices[0]
                if isinstance(first_choice, dict) and first_choice.get('message') and isinstance(first_choice['message'], dict):
                    # Content can be an empty string, which is valid structurally but semantically empty.
                    enhanced_text_raw = first_choice['message'].get('content')
                    
                    if enhanced_text_raw is not None: # content field exists
                        enhanced_text = enhanced_text_raw.strip()
                        if not enhanced_text: # Content was empty string or just whitespace
                            self.logger.warning(f"LLM (direct HTTP) for segment {seg_idx} ('{original_text[:30]}...') returned semantically empty content. Falling back to original.")
                            return {"text": original_text, "start": seg.get("start"), "end": seg.get("end")}
                        
                        self.logger.debug(f"Segment {seg_idx}: Original: '{original_text}' -> Enhanced (direct HTTP): '{enhanced_text}'")
                        return {"text": enhanced_text, "start": seg.get("start"), "end": seg.get("end")}
                    else: # 'content' field is missing from message
                        self.logger.error(f"LLM enhancement (direct HTTP) for segment {seg_idx} ('{original_text[:30]}...'). 'content' field missing in message.")
                        self.logger.error(f"Message object received: {str(first_choice['message'])[:500]}")
                        raise ValueError("Missing 'content' in LLM API response message (direct HTTP)")
                else: # 'message' field missing or not a dict
                    self.logger.error(f"LLM enhancement (direct HTTP) for segment {seg_idx} ('{original_text[:30]}...'). 'message' field missing or invalid in choice.")
                    self.logger.error(f"Choice object received: {str(first_choice)[:500]}")
                    raise ValueError("Invalid 'message' field in LLM API response choice (direct HTTP)")
            else: # 'choices' field missing, not a list, or empty
                self.logger.error(f"LLM enhancement (direct HTTP) for segment {seg_idx} ('{original_text[:30]}...'). 'choices' array missing, invalid, or empty.")
                self.logger.error(f"Response JSON received: {str(response_data)[:500]}")
                raise ValueError("Invalid 'choices' array in LLM API response (direct HTTP)")

        except httpx.HTTPStatusError as e:
            self.logger.error(f"LLM enhancement (direct HTTP) failed for segment {seg_idx} ('{original_text[:30]}...') with HTTP status {e.response.status_code}.")
            # Attempt to log JSON error response if possible
            error_response_text = e.response.text
            try:
                error_details = e.response.json()
                self.logger.error(f"Error details from JSON response: {error_details}")
            except json.JSONDecodeError:
                self.logger.error(f"Could not decode JSON from error response. Raw response snippet: {error_response_text[:500]}")

            # Grok's suggestion: Simple retry for rate limiting (429)
            # We need to ensure this retry logic is well-contained.
            # This is a simplified version without tracking retry counts for now.
            # A more robust solution would involve a retry counter and exponential backoff.
            if e.response.status_code == 429:
                # Check if a retry has already been attempted for this segment to avoid infinite loops
                # This requires passing a retry_attempted flag or similar state, which complicates things.
                # For now, a single, simple retry. If this becomes a common issue, enhance retry logic.
                self.logger.warning(f"Rate limit (429) encountered for segment {seg_idx}. Retrying once after 1 second...")
                await asyncio.sleep(1)
                # To call itself again, we need to handle the original segment `seg` and `seg_idx`.
                # This recursive call could be problematic if not careful.
                # A loop structure for retries within this function would be safer.
                # For simplicity in this step, we'll just log and raise. A full retry needs more structure.
                # If we were to implement a single retry:
                # try:
                #    self.logger.info(f"Retrying segment {seg_idx} after rate limit...")
                #    return await self._process_segment_async(seg, seg_idx, retry_attempted=True) # Needs retry_attempted param
                # except Exception as retry_e:
                #    self.logger.error(f"Retry for segment {seg_idx} also failed: {retry_e}", exc_info=True)
                #    raise retry_e from e # Chain the exception
                # For now, just re-raise the original error after logging details
                self.logger.error(f"Rate limit hit for segment {seg_idx}. Not retrying with current simple logic. Original error details logged above.")

            raise # Re-raise the original HTTPStatusError to be caught by asyncio.gather
        
        except httpx.RequestError as e: # Covers network errors, DNS failures, timeouts not covered by HTTPStatusError
            self.logger.error(f"LLM enhancement (direct HTTP) request failed for segment {seg_idx} ('{original_text[:30]}...'): {e}", exc_info=True)
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"LLM enhancement (direct HTTP) failed to decode JSON response for segment {seg_idx} ('{original_text[:30]}...'). Raw response: {response.text[:500] if 'response' in locals() else 'N/A'}", exc_info=True)
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during LLM enhancement (direct HTTP) for segment {seg_idx} ('{original_text[:30]}...'): {e}", exc_info=True)
            raise

    async def close_http_client(self):
        """Closes the httpx client. Should be called on application shutdown."""
        if hasattr(self, 'http_client') and self.http_client:
            try:
                await self.http_client.aclose()
                self.logger.info("LLMEnhancer: HTTP client closed successfully.")
            except Exception as e:
                self.logger.error(f"LLMEnhancer: Error closing HTTP client: {e}", exc_info=True)