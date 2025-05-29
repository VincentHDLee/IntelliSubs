# LLM Text Enhancement Utilities

import httpx # For direct HTTP requests
import asyncio
import logging
import json # For parsing JSON response

class LLMEnhancer:
    # Define a max length for script context to prevent excessive token usage initially
    MAX_SCRIPT_CONTEXT_LENGTH = 4000 # Characters, roughly 1k tokens

    def __init__(self, api_key: str, model_name: str = "gpt-3.5-turbo", base_url: str = None,
                 language: str = "ja", logger: logging.Logger = None, script_context: str = None,
                 system_prompt: str = None):
        """
        Initializes the LLMEnhancer for direct HTTP POST requests.

        Args:
            api_key (str): The API key for the LLM service.
            model_name (str): The name of the LLM model to use.
            base_url (str, optional): The base domain provided by the user (e.g., https://api.openai.com).
                                     Standard OpenAI paths like /v1/chat/completions will be appended.
            language (str): Language of the text to be enhanced (e.g., "ja").
            logger (logging.Logger, optional): Logger instance.
            script_context (str, optional): Full text content of an imported script.
            system_prompt (str, optional): User-defined system prompt.
        """
        self.logger = logger if logger else logging.getLogger(self.__class__.__name__)
        self.model_name = model_name
        self.language = language
        self.api_key = api_key
        self.api_key_provided = bool(api_key)
        
        self.script_context = None
        if script_context:
            if len(script_context) > self.MAX_SCRIPT_CONTEXT_LENGTH:
                self.logger.warning(f"Provided script_context exceeds max length ({self.MAX_SCRIPT_CONTEXT_LENGTH} chars). Truncating.")
                self.script_context = script_context[:self.MAX_SCRIPT_CONTEXT_LENGTH]
            else:
                self.script_context = script_context
            self.logger.info(f"LLMEnhancer initialized with script_context, length: {len(self.script_context)} chars.")
        else:
            self.logger.info("LLMEnhancer initialized without script_context.")
        
        self.system_prompt = system_prompt.strip() if system_prompt else None
        if self.system_prompt:
            self.logger.info(f"LLMEnhancer initialized with user-defined system_prompt, length: {len(self.system_prompt)} chars.")
        else:
            self.logger.info("LLMEnhancer initialized without user-defined system_prompt (will use default).")

        self.base_url = "" # Renamed from base_domain_for_requests for clarity
        if isinstance(base_url, str) and base_url.strip():
            # Store the base URL, ensuring no trailing slash for consistent path joining.
            self.base_url = base_url.strip().rstrip('/')
            self.logger.info(f"LLMEnhancer: Base URL for LLM requests: '{self.base_url}'.")
        else:
            self.logger.warning("LLMEnhancer: Base URL not provided or invalid. LLM calls will likely fail.")

        if not self.api_key_provided:
            self.logger.warning("LLMEnhancer: API key not provided. Enhancement and model fetching might be unavailable.")

        self.logger.info(f"LLMEnhancer setup complete. Model: {model_name}, Lang: {language}, API Key Provided: {self.api_key_provided}, Base URL: '{self.base_url}', Script Context: {bool(self.script_context)}, System Prompt: {bool(self.system_prompt)}")

    def set_language(self, lang_code: str):
        """Sets the active language for LLM prompts."""
        new_lang = lang_code.lower()
        if self.language != new_lang:
            self.language = new_lang
            self.logger.info(f"LLMEnhancer language set to: '{self.language}'")
        else:
            self.logger.debug(f"LLMEnhancer language already set to: '{self.language}', no change.")

    def update_config(self, api_key: str = None, model_name: str = None, base_url: str = None,
                      language: str = None, script_context: str = None, system_prompt: str = None):
        """
        Updates the configuration of the LLMEnhancer instance.
        Only provided parameters will be updated.
        """
        self.logger.info("LLMEnhancer.update_config called.")
        updated_fields = []

        if api_key is not None and self.api_key != api_key:
            self.api_key = api_key
            self.api_key_provided = bool(api_key)
            updated_fields.append("api_key")

        if model_name is not None and self.model_name != model_name:
            self.model_name = model_name
            updated_fields.append("model_name")

        if base_url is not None:
            cleaned_base_url = base_url.strip().rstrip('/') if isinstance(base_url, str) and base_url.strip() else ""
            if self.base_url != cleaned_base_url:
                self.base_url = cleaned_base_url
                updated_fields.append("base_url")
        
        if language is not None and self.language != language.lower():
            self.set_language(language)
            updated_fields.append("language")

        if script_context is not None:
            new_script_context = None
            if script_context:
                if len(script_context) > self.MAX_SCRIPT_CONTEXT_LENGTH:
                    self.logger.warning(f"Provided script_context in update_config exceeds max length. Truncating.")
                    new_script_context = script_context[:self.MAX_SCRIPT_CONTEXT_LENGTH]
                else:
                    new_script_context = script_context
            
            if self.script_context != new_script_context:
                self.script_context = new_script_context
                updated_fields.append("script_context")
                self.logger.info(f"LLMEnhancer script_context updated, new length: {len(self.script_context) if self.script_context else 0} chars.")

        if system_prompt is not None:
            new_system_prompt = system_prompt.strip() if system_prompt else None
            if self.system_prompt != new_system_prompt:
                self.system_prompt = new_system_prompt
                updated_fields.append("system_prompt")
                self.logger.info(f"LLMEnhancer system_prompt updated, new length: {len(self.system_prompt) if self.system_prompt else 0} chars.")

        if updated_fields:
            self.logger.info(f"LLMEnhancer configuration updated for fields: {', '.join(updated_fields)}.")
            self.logger.info(f"LLMEnhancer new state: model={self.model_name}, lang={self.language}, API Key Provided={self.api_key_provided}, Base URL='{self.base_url}', Script Context={bool(self.script_context)}, System Prompt={bool(self.system_prompt)}")
        else:
            self.logger.info("LLMEnhancer.update_config: No configuration fields were changed.")

    async def async_enhance_text_segments(self, text_segments: list) -> list:
        """
        Asynchronously enhances text segments using direct HTTP POST requests.
        """
        if not self.api_key_provided :
            self.logger.warning("LLM enhancement skipped: API key not provided.")
            return text_segments
        # Ensure base_url is set if we are attempting to use LLM
        if not self.base_url:
             self.logger.warning("LLM enhancement skipped: Base URL not provided.")
             return text_segments

        self.logger.info(f"Starting async LLM ({self.model_name}) enhancement for {len(text_segments)} text segments (direct HTTP).")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            tasks = []
            for seg_idx, seg in enumerate(text_segments):
                # Pass the client to the processing method
                tasks.append(self._process_segment_async(client, seg, seg_idx))
            
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

    async def _process_segment_async(self, client: httpx.AsyncClient, seg: dict, seg_idx: int) -> dict:
        """
        Asynchronously processes a single text segment by making a direct HTTP POST request
        to an OpenAI-compatible Chat Completions endpoint, using the provided httpx client.
        The target URL is constructed from base_domain_for_requests + "/v1/chat/completions".
        """
        original_text = seg.get("text", "")
        if not original_text.strip():
            return seg # Return original segment if text is empty
            
        # Construct the target URL by appending the standard OpenAI path to the base_url
        target_url = f"{self.base_url}/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        system_prompt_content = ""
        user_prompt_content = ""

        if self.system_prompt:
            system_prompt_content = self.system_prompt
            self.logger.debug(f"Segment {seg_idx}: Using user-defined system_prompt.")
        elif self.language == "ja":
            system_prompt_content = (
                "あなたは日本語のビデオ字幕編集の専門家です。"
                "以下のテキストを自然で読みやすい日本語字幕に最適化し、句読点を適切に調整し、明瞭さを向上させてください。"
                "必ず結果を返し、空の応答を避けてください。\n"
                "例: 入力: 'こんにちは皆さん元気？' → 出力: 'こんにちは、皆さん。元気ですか？'"
            )
            user_prompt_content = f"テキスト：「{original_text}」"
            
        elif self.language == "zh":
            system_prompt_content = (
                "你是一位专业的视频字幕编辑。请优化以下文本，使其成为自然流畅、标点准确的简体中文视频字幕。"
                "主要任务包括：修正明显的ASR识别错误（如果能判断），补全或修正标点符号（特别是句号、逗号、问号），"
                "并确保文本在语义上通顺且易于阅读。请直接返回优化后的字幕文本，确保结果非空。\n"
                "输入示例：'大家好今天天气不错我们去公园玩吧' -> 输出示例：'大家好，今天天气不错。我们去公园玩吧！'"
            )
            user_prompt_content = f"原始文本：“{original_text}”"

        else: # Fallback for English or other unspecified languages
            system_prompt_content = (
                "You are an expert in subtitle editing. Optimize the following text for natural, readable subtitles, "
                "adjusting punctuation and improving clarity. Ensure a result is returned and avoid empty responses.\n"
                "Example: Input: 'hello everyone hows it going' -> Output: 'Hello, everyone. How's it going?'"
            )
            user_prompt_content = f"Text: \"{original_text}\""

        # Prepend script context to system prompt if available
        if self.script_context:
            context_prefix = f"以下是作为参考的完整剧本或相关上下文信息：\n\"\"\"\n{self.script_context}\n\"\"\"\n请基于以上上下文和你的专业知识进行优化。\n\n---\n\n"
            system_prompt_content = context_prefix + system_prompt_content
            self.logger.debug(f"Segment {seg_idx}: Using script_context (length: {len(self.script_context)}) in system prompt.")

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt_content},
                {"role": "user", "content": user_prompt_content}
            ],
            "temperature": 0.3,
            "max_tokens": max(300, int(len(original_text) * 3) + 100)
        }
        
        self.logger.info(f"Segment {seg_idx}: Sending direct HTTP POST to {target_url} for LLM enhancement (using appended /v1/chat/completions).")
        self.logger.debug(f"Segment {seg_idx}: Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")

        try:
            response = await client.post(target_url, json=payload, headers=headers)
            response.raise_for_status()
            response_data = response.json()
            self.logger.debug(f"Segment {seg_idx}: Full API response data from {target_url}: {json.dumps(response_data, ensure_ascii=False, indent=2)}")

            choices = response_data.get('choices')
            if choices and isinstance(choices, list) and len(choices) > 0:
                first_choice = choices[0]
                if isinstance(first_choice, dict) and first_choice.get('message') and isinstance(first_choice['message'], dict):
                    enhanced_text_raw = first_choice['message'].get('content')
                    
                    if enhanced_text_raw is not None:
                        enhanced_text = enhanced_text_raw.strip()
                        if not enhanced_text:
                            self.logger.warning(f"LLM (direct HTTP {target_url}) for segment {seg_idx} ('{original_text[:30]}...') returned semantically empty content. Falling back to original.")
                            return {"text": original_text, "start": seg.get("start"), "end": seg.get("end")}
                        
                        self.logger.debug(f"Segment {seg_idx}: Original: '{original_text}' -> Enhanced (direct HTTP {target_url}): '{enhanced_text}'")
                        return {"text": enhanced_text, "start": seg.get("start"), "end": seg.get("end")}
                    else:
                        self.logger.error(f"LLM enhancement (direct HTTP {target_url}) for segment {seg_idx} ('{original_text[:30]}...'). 'content' field missing in message.")
                        self.logger.error(f"Message object received: {str(first_choice['message'])[:500]}")
                        raise ValueError(f"Missing 'content' in LLM API response message (direct HTTP {target_url})")
                else:
                    self.logger.error(f"LLM enhancement (direct HTTP {target_url}) for segment {seg_idx} ('{original_text[:30]}...'). 'message' field missing or invalid in choice.")
                    self.logger.error(f"Choice object received: {str(first_choice)[:500]}")
                    raise ValueError(f"Invalid 'message' field in LLM API response choice (direct HTTP {target_url})")
            else:
                self.logger.error(f"LLM enhancement (direct HTTP {target_url}) for segment {seg_idx} ('{original_text[:30]}...'). 'choices' array missing, invalid, or empty.")
                self.logger.error(f"Response JSON received: {str(response_data)[:500]}")
                raise ValueError(f"Invalid 'choices' array in LLM API response (direct HTTP {target_url})")

        except httpx.HTTPStatusError as e:
            self.logger.error(f"LLM enhancement (direct HTTP {target_url}) failed for segment {seg_idx} ('{original_text[:30]}...') with HTTP status {e.response.status_code}.")
            error_response_text = e.response.text
            try:
                error_details = e.response.json()
                self.logger.error(f"Error details from JSON response: {error_details}")
            except json.JSONDecodeError:
                self.logger.error(f"Could not decode JSON from error response. Raw response snippet: {error_response_text[:500]}")

            if e.response.status_code == 429:
                self.logger.warning(f"Rate limit (429) encountered for segment {seg_idx}. Retrying once after 1 second...")
                await asyncio.sleep(1)
                self.logger.error(f"Rate limit hit for segment {seg_idx}. Not retrying with current simple logic. Original error details logged above.")
            raise
        
        except httpx.RequestError as e:
            self.logger.error(f"LLM enhancement (direct HTTP) request failed for segment {seg_idx} ('{original_text[:30]}...'): {e}", exc_info=True)
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"LLM enhancement (direct HTTP) failed to decode JSON response for segment {seg_idx} ('{original_text[:30]}...'). Raw response: {response.text[:500] if 'response' in locals() else 'N/A'}", exc_info=True)
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during LLM enhancement (direct HTTP) for segment {seg_idx} ('{original_text[:30]}...'): {e}", exc_info=True)
            raise

    async def async_get_available_models(self) -> list[str]:
        """
        Asynchronously fetches the list of available model IDs from base_url + /v1/models endpoint.
        """
        if not self.base_url:
            self.logger.warning("Cannot fetch models: Base URL is not configured.")
            return []
        
        # API key might still be needed.
        # if not self.api_key_provided:
        # self.logger.warning("API key not provided, model fetching might fail if required by the endpoint.")

        target_url = f"{self.base_url}/v1/models" # Append standard path
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        self.logger.info(f"Fetching available models from: {target_url}")
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.get(target_url, headers=headers)
                response.raise_for_status()
                response_data = response.json()
                self.logger.debug(f"Full API response data from {target_url} (using appended /v1/models): {json.dumps(response_data, ensure_ascii=False, indent=2)}")

                models = []
                if isinstance(response_data, dict) and 'data' in response_data and isinstance(response_data['data'], list):
                    for model_info in response_data['data']:
                        if isinstance(model_info, dict) and 'id' in model_info:
                            models.append(model_info['id'])
                elif isinstance(response_data, list): # Some APIs might return a list of strings or objects directly
                    for item in response_data:
                        if isinstance(item, str):
                            models.append(item)
                        elif isinstance(item, dict) and 'id' in item:
                             models.append(item['id'])
                else:
                    self.logger.warning(f"Unexpected format for {target_url} response. Expected dict with 'data' list or a list. Got: {type(response_data)}")

                if not models:
                     self.logger.warning(f"No models found or 'data' array missing/empty in response from {target_url}.")
                else:
                    self.logger.info(f"Successfully fetched {len(models)} models from {target_url}: {models}")
                return sorted(list(set(models)))

            except httpx.HTTPStatusError as e:
                self.logger.error(f"Failed to fetch models from {target_url}. HTTP status: {e.response.status_code}.")
                error_response_text = e.response.text
                try:
                    error_details = e.response.json()
                    self.logger.error(f"Error details from JSON response: {error_details}")
                except json.JSONDecodeError:
                    self.logger.error(f"Could not decode JSON from error response. Raw response snippet: {error_response_text[:500]}")
                return []
            except httpx.RequestError as e:
                self.logger.error(f"Request failed while fetching models from {target_url}: {e}", exc_info=True)
                return []
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to decode JSON response while fetching models from {target_url}. Raw response: {response.text[:500] if 'response' in locals() else 'N/A'}", exc_info=True)
                return []
            except Exception as e:
                self.logger.error(f"Unexpected error while fetching models from {target_url}: {e}", exc_info=True)
                return []

    async def close_http_client(self):
        """
        Closes the httpx client. Should be called on application shutdown.
        NOTE: With client created per-call in async_enhance_text_segments and async_get_available_models,
        this method is mostly a placeholder unless a persistent client is reintroduced.
        """
        self.logger.debug("LLMEnhancer.close_http_client called. Clients are managed per-call.")
        pass

    async def async_test_chat_completion(self) -> tuple[bool, str]:
        """
        Asynchronously tests the chat completion endpoint with a simple "Hello" message.
        Returns:
            tuple[bool, str]: (success_status, message)
        """
        if not self.api_key_provided:
            msg = "API Key 未提供。"
            self.logger.warning(f"LLM Chat Test Skipped: {msg}")
            return False, msg
        if not self.base_url:
            msg = "Base URL 未配置。"
            self.logger.warning(f"LLM Chat Test Skipped: {msg}")
            return False, msg

        target_url = f"{self.base_url}/v1/chat/completions"
        self.logger.info(f"Attempting LLM chat test to: {target_url}")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name if self.model_name else "gpt-3.5-turbo", # Use configured model or a default
            "messages": [{"role": "user", "content": "Hello"}],
            "temperature": 0.7,
            "max_tokens": 50
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                response = await client.post(target_url, json=payload, headers=headers)
                response.raise_for_status() # Raises HTTPStatusError for 4xx/5xx
                response_data = response.json()
                
                choices = response_data.get('choices')
                if choices and isinstance(choices, list) and len(choices) > 0:
                    first_choice = choices[0]
                    if isinstance(first_choice, dict) and first_choice.get('message') and \
                       isinstance(first_choice['message'], dict) and first_choice['message'].get('content'):
                        self.logger.info(f"LLM chat test successful. Response: {first_choice['message']['content'][:50]}...")
                        return True, "聊天端点连接成功并收到回复。"
                    else:
                        self.logger.warning(f"LLM chat test: Response format invalid. Message or content missing. Response: {str(response_data)[:200]}")
                        return False, "聊天端点连接成功，但回复格式无效。"
                else:
                    self.logger.warning(f"LLM chat test: 'choices' array missing or empty. Response: {str(response_data)[:200]}")
                    return False, "聊天端点连接成功，但回复中缺少 'choices'。"

            except httpx.HTTPStatusError as e:
                error_body = e.response.text
                try:
                    error_details = e.response.json()
                    error_body = json.dumps(error_details)
                except json.JSONDecodeError:
                    pass # Keep raw text
                self.logger.error(f"LLM chat test failed: HTTP {e.response.status_code} from {target_url}. Response: {error_body[:200]}")
                return False, f"聊天端点连接失败 (HTTP {e.response.status_code}): {error_body[:100]}"
            except httpx.RequestError as e:
                self.logger.error(f"LLM chat test failed: Request error to {target_url}: {e}", exc_info=True)
                return False, f"聊天端点请求错误: {e}"
            except Exception as e:
                self.logger.error(f"LLM chat test failed: Unexpected error with {target_url}: {e}", exc_info=True)
                return False, f"聊天端点连接时发生意外错误: {e}"