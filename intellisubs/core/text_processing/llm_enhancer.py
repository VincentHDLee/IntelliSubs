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
                 user_override_system_prompt: str = None, # Renamed for clarity
                 config_prompts: dict = None): # New parameter for prompts from config.json
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
            user_override_system_prompt (str, optional): User-defined system prompt from UI settings.
            config_prompts (dict, optional): Dictionary containing default prompts loaded from config
                                             (e.g., {"ja": {"system": "...", "user_template": "..."}}).
        """
        self.logger = logger if logger else logging.getLogger(self.__class__.__name__)
        self.config_prompts = config_prompts if config_prompts else {} # Store prompts from config
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
        
        self.user_override_system_prompt = user_override_system_prompt.strip() if user_override_system_prompt else None
        if self.user_override_system_prompt:
            self.logger.info(f"LLMEnhancer initialized with user-override system_prompt, length: {len(self.user_override_system_prompt)} chars.")
        else:
            self.logger.info("LLMEnhancer initialized without user-override system_prompt (will use configured or hardcoded default).")

        self.base_url = "" # Renamed from base_domain_for_requests for clarity
        if isinstance(base_url, str) and base_url.strip():
            # Store the base URL, ensuring no trailing slash for consistent path joining.
            self.base_url = base_url.strip().rstrip('/')
            self.logger.info(f"LLMEnhancer: Base URL for LLM requests: '{self.base_url}'.")
        else:
            self.logger.warning("LLMEnhancer: Base URL not provided or invalid. LLM calls will likely fail.")

        if not self.api_key_provided:
            self.logger.warning("LLMEnhancer: API key not provided. Enhancement and model fetching might be unavailable.")

        self.logger.info(f"LLMEnhancer setup complete. Model: {model_name}, Lang: {language}, API Key Provided: {self.api_key_provided}, Base URL: '{self.base_url}', Script Context: {bool(self.script_context)}, User Override System Prompt: {bool(self.user_override_system_prompt)}")

    def set_language(self, lang_code: str):
        """Sets the active language for LLM prompts."""
        new_lang = lang_code.lower()
        if self.language != new_lang:
            self.language = new_lang
            self.logger.info(f"LLMEnhancer language set to: '{self.language}'")
        else:
            self.logger.debug(f"LLMEnhancer language already set to: '{self.language}', no change.")

    def update_config(self, api_key: str = None, model_name: str = None, base_url: str = None,
                      language: str = None, script_context: str = None,
                      user_override_system_prompt: str = None, # Renamed
                      config_prompts: dict = None): # Added
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

        if user_override_system_prompt is not None:
            new_user_override_system_prompt = user_override_system_prompt.strip() if user_override_system_prompt else None
            if self.user_override_system_prompt != new_user_override_system_prompt:
                self.user_override_system_prompt = new_user_override_system_prompt
                updated_fields.append("user_override_system_prompt")
                self.logger.info(f"LLMEnhancer user_override_system_prompt updated, new length: {len(self.user_override_system_prompt) if self.user_override_system_prompt else 0} chars.")

        if config_prompts is not None and self.config_prompts != config_prompts:
            self.config_prompts = config_prompts
            updated_fields.append("config_prompts")
            self.logger.info(f"LLMEnhancer config_prompts updated.")


        if updated_fields:
            self.logger.info(f"LLMEnhancer configuration updated for fields: {', '.join(updated_fields)}.")
            self.logger.info(f"LLMEnhancer new state: model={self.model_name}, lang={self.language}, API Key Provided={self.api_key_provided}, Base URL='{self.base_url}', Script Context={bool(self.script_context)}, User Override System Prompt={bool(self.user_override_system_prompt)}")
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
        user_prompt_content = "" # Will be set based on template

        # Determine System Prompt: User Override > Configured Default > Hardcoded Default
        if self.user_override_system_prompt:
            system_prompt_content = self.user_override_system_prompt
            self.logger.debug(f"Segment {seg_idx}: Using user-override system_prompt.")
        elif self.config_prompts.get(self.language, {}).get("system"):
            system_prompt_content = self.config_prompts[self.language]["system"]
            self.logger.debug(f"Segment {seg_idx}: Using system_prompt from config for language '{self.language}'.")
        else: # Fallback to hardcoded defaults
            self.logger.debug(f"Segment {seg_idx}: Using hardcoded default system_prompt for language '{self.language}'.")
            if self.language == "ja":
                system_prompt_content = (
                    "あなたは日本語のビデオ字幕編集の専門家です。"
                    "以下のテキストを自然で読みやすい日本語字幕に最適化し、句読点を適切に調整し、明瞭さを向上させてください。"
                    "応答には最適化された字幕テキスト「のみ」を含めてください。説明、マークダウン、書式設定、または「最適化された字幕:」のようなラベルは一切含めないでください。"
                    "必ず結果を返し、空の応答を避けてください。\n"
                    "例: 入力: 'こんにちは皆さん元気？' → 出力: 'こんにちは、皆さん。元気ですか？'"
                )
            elif self.language == "zh":
                system_prompt_content = (
                    "你是一位专业的视频字幕编辑。请优化以下文本，使其成为自然流畅、标点准确的简体中文视频字幕。"
                    "主要任务包括：修正明显的ASR识别错误（如果能判断），补全或修正标点符号（特别是句号、逗号、问号），"
                    "并确保文本在语义上通顺且易于阅读。"
                    "返回结果时，请「仅」包含优化后的字幕文本。不要添加任何解释、markdown、格式化内容或类似“优化字幕:”的标签。"
                    "请确保结果非空。\n"
                    "输入示例：'大家好今天天气不错我们去公园玩吧' -> 输出示例：'大家好，今天天气不错。我们去公园玩吧！'"
                )
            else: # Fallback for English or other unspecified languages
                system_prompt_content = (
                    "You are an expert in subtitle editing. Optimize the following text for natural, readable subtitles, "
                    "adjusting punctuation and improving clarity. "
                    "In your response, include *only* the optimized subtitle text. Do not add any explanations, markdown, formatting, or labels like 'Optimized Subtitle:'."
                    "Ensure a result is returned and avoid empty responses.\n"
                    "Example: Input: 'hello everyone hows it going' -> Output: 'Hello, everyone. How's it going?'"
                )

        # Determine User Prompt Template: Configured Default > Hardcoded Default
        user_prompt_template = ""
        if self.config_prompts.get(self.language, {}).get("user_template"):
            user_prompt_template = self.config_prompts[self.language]["user_template"]
            self.logger.debug(f"Segment {seg_idx}: Using user_prompt_template from config for language '{self.language}'.")
        else: # Fallback to hardcoded defaults
            self.logger.debug(f"Segment {seg_idx}: Using hardcoded default user_prompt_template for language '{self.language}'.")
            if self.language == "ja":
                user_prompt_template = "テキスト：「{text_to_enhance}」"
            elif self.language == "zh":
                user_prompt_template = "原始文本：“{text_to_enhance}”"
            else: # Fallback for English or other unspecified languages
                user_prompt_template = "Text: \"{text_to_enhance}\""
        
        user_prompt_content = user_prompt_template.format(text_to_enhance=original_text)

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
                        # --- BEGIN RESPONSE PARSING ---
                        cleaned_text = self._parse_llm_response_content(enhanced_text_raw)
                        # --- END RESPONSE PARSING ---

                        if not cleaned_text: # If parsing results in empty string
                            self.logger.warning(f"LLM (direct HTTP {target_url}) for segment {seg_idx} ('{original_text[:30]}...') returned empty or unparsable content after cleaning. Falling back to original. Raw: '{enhanced_text_raw[:100]}'")
                            return {"text": original_text, "start": seg.get("start"), "end": seg.get("end")}
                        
                        self.logger.debug(f"Segment {seg_idx}: Original: '{original_text}' -> Parsed Enhanced (direct HTTP {target_url}): '{cleaned_text}' (Raw: '{enhanced_text_raw[:100]}...')")
                        return {"text": cleaned_text, "start": seg.get("start"), "end": seg.get("end")}
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

    def _parse_llm_response_content(self, raw_content: str) -> str:
        """
        Parses the raw LLM response content to extract only the subtitle text.
        Attempts to remove common headers, explanations, and markdown.
        """
        self.logger.debug(f"Parsing LLM raw response (first 200 chars): '{raw_content[:200]}'")
        lines = raw_content.splitlines()
        
        # Potential headers or patterns indicating the start of the actual subtitle
        subtitle_markers_ja = ["「", "『"] # Japanese quotes
        subtitle_markers_common = ['"'] # Common quotes
        
        # Patterns indicating explanations or non-subtitle content
        explanation_keywords_ja = ["**最適化された字幕:**", "**調整ポイント:**", "最適化された字幕:", "調整ポイント:", "句読点の修正", "読みやすさの向上", "語尾の自然さ"]
        explanation_keywords_en = ["**Optimized Subtitle:**", "**Adjustment Points:**", "Optimized Subtitle:", "Adjustment Points:", "Punctuation correction", "Improved readability"]
        explanation_keywords_zh = ["**优化字幕:**", "**调整点:**", "优化字幕:", "调整点:", "标点修正", "可读性提升"]

        all_explanation_keywords = explanation_keywords_ja + explanation_keywords_en + explanation_keywords_zh

        extracted_subtitle_lines = []
        in_subtitle_block = False
        found_subtitle_marker_on_line = False

        # First pass: Try to find explicit subtitle block if markers like "最適化された字幕:" are present
        possible_subtitle_content = raw_content
        for keyword in explanation_keywords_ja + explanation_keywords_en + explanation_keywords_zh:
            if keyword in raw_content:
                # If a keyword like "最適化された字幕:" is found, try to take text after it
                # This is a simple heuristic and might need refinement
                parts = raw_content.split(keyword, 1)
                if len(parts) > 1:
                    # Take the part after the keyword, split by lines, and find first non-empty content
                    potential_block = parts[1].strip()
                    block_lines = potential_block.splitlines()
                    for line in block_lines:
                        line = line.strip()
                        if line: # Take the first non-empty line
                             # Check if this line itself is another explanation keyword
                            if not any(exp_kw in line for exp_kw in all_explanation_keywords):
                                possible_subtitle_content = line
                                self.logger.debug(f"Parser: Found content '{line}' after keyword '{keyword}'.")
                                break # Found a candidate line
                            else: # This line is another header, so the content wasn't immediately after.
                                self.logger.debug(f"Parser: Line '{line}' after '{keyword}' is another explanation keyword. Resetting block.")
                                possible_subtitle_content = "" # Reset, this wasn't it
                                break
                        # if we continue, it means we are looking for first non-empty line
                    if possible_subtitle_content: # If we found something after a specific marker
                        # Check if this content itself contains an explanation block
                        for exp_kw in all_explanation_keywords:
                            if exp_kw in possible_subtitle_content:
                                possible_subtitle_content = possible_subtitle_content.split(exp_kw)[0].strip()
                                self.logger.debug(f"Parser: Further refined content to '{possible_subtitle_content}' by splitting at '{exp_kw}'.")
                        
                        if possible_subtitle_content.strip(): # If after all this, we have something.
                             # Remove common markdown like **
                            cleaned = possible_subtitle_content.replace("**", "").strip()
                            self.logger.info(f"Parser: Extracted subtitle using keyword heuristic: '{cleaned}' from raw (first 100): '{raw_content[:100]}'")
                            return cleaned
        
        # If keyword-based extraction didn't yield a clear result, try line-by-line processing
        self.logger.debug("Parser: Keyword heuristic didn't yield a clear result, or no keywords found. Proceeding with line-by-line parsing.")
        
        for line_idx, line in enumerate(lines):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                if in_subtitle_block and extracted_subtitle_lines: # Treat blank line as end of subtitle block
                    self.logger.debug(f"Parser: Empty line after content, assuming end of subtitle block. Line: {line_idx}")
                    break
                continue

            # Check for explanation keywords
            if any(exp_kw in line for exp_kw in all_explanation_keywords):
                self.logger.debug(f"Parser: Explanation keyword found on line {line_idx}: '{line}'.")
                if in_subtitle_block and extracted_subtitle_lines: # If we were in a block, this ends it
                    self.logger.debug(f"Parser: Explanation keyword ends current subtitle block.")
                    break
                continue # Skip this line

            # If not an explanation, consider it part of subtitle
            # This is a more greedy approach if explicit markers are not found or are ambiguous
            
            # Attempt to remove markdown like **
            line = line.replace("**", "")

            # Simple check for quotes to identify potential subtitle lines
            # This helps if the model *only* returns the quoted subtitle.
            is_quoted_line = False
            for quote in subtitle_markers_ja + subtitle_markers_common:
                if line.startswith(quote) and line.endswith(quote) and len(line) > 1:
                    line = line[len(quote):-len(quote)].strip() # Remove surrounding quotes
                    is_quoted_line = True
                    break
            
            if is_quoted_line :
                 extracted_subtitle_lines.append(line)
                 self.logger.debug(f"Parser: Added quoted line {line_idx} as subtitle: '{line}'")
                 in_subtitle_block = True # Once we find a quoted line, assume it's a subtitle
                 # If we expect single-line subtitles, we can break here.
                 # For multi-line, we'd continue if the next line is also part of it.
                 # Given typical LLM behavior for this task, a single line is common.
                 break # Assume one-liner subtitle from quoted response

            elif not extracted_subtitle_lines: # If no lines extracted yet, take the first non-explanation line
                extracted_subtitle_lines.append(line)
                in_subtitle_block = True
                self.logger.debug(f"Parser: Added first non-explanation line {line_idx} as potential subtitle: '{line}'")
                # If a subsequent line is an explanation, this block will end.
                # If we expect single-line, could break here too. For now, allow multi-line until explanation.
            
            elif in_subtitle_block: # Already in a block, and not an explanation line
                 extracted_subtitle_lines.append(line)
                 self.logger.debug(f"Parser: Added subsequent line {line_idx} to subtitle block: '{line}'")


        if not extracted_subtitle_lines:
            # Fallback: if nothing specific extracted, return the first non-empty line of the original raw_content, stripped
            self.logger.warning(f"Parser: No specific subtitle content extracted. Falling back to first non-empty line of raw input or full raw input if simple. Raw (first 100): '{raw_content[:100]}'")
            first_non_empty_line = next((l.strip() for l in raw_content.splitlines() if l.strip()), "").replace("**", "")
            return first_non_empty_line if first_non_empty_line else raw_content.strip().replace("**", "")


        final_text = " ".join(extracted_subtitle_lines).strip()
        self.logger.info(f"Parser: Final extracted text: '{final_text}' from raw (first 100): '{raw_content[:100]}'")
        return final_text

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