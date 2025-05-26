# Core Workflow Manager for IntelliSubs

from .asr_services.whisper_service import WhisperService
from .audio_processing.processor import AudioProcessor
from .text_processing.normalizer import ASRNormalizer
from .text_processing.punctuator import Punctuator
from .text_processing.segmenter import SubtitleSegmenter
from .text_processing.llm_enhancer import LLMEnhancer
from .subtitle_formats.srt_formatter import SRTFormatter
from .subtitle_formats.lrc_formatter import LRCFormatter
from .subtitle_formats.ass_formatter import ASSFormatter
from .subtitle_formats.txt_formatter import TxtFormatter

import os
import tempfile
import logging
import asyncio # Added for running async LLM enhancer
from intellisubs.utils.logger_setup import mask_sensitive_data
import pysrt

# import os # Placeholder
# import tempfile # Placeholder

class WorkflowManager:
    def __init__(self, config: dict = None, logger: logging.Logger = None):
        """
        Initializes the WorkflowManager. Accepts a logger instance.

        Args:
            config (dict, optional): Configuration dictionary for various components.
                                     Example: {
                                         "asr_model": "small", "device": "cpu",
                                         "llm_enabled": False, "llm_api_key": "...",
                                         "custom_dict_path": "path/to/dict.csv"
                                     }
        """
        self.config = config if config else {}
        self.logger = logger if logger else logging.getLogger(__name__) # Use provided logger or get a new one
        # Mask sensitive data before logging
        masked_config_for_log = mask_sensitive_data(self.config)
        self.logger.info(f"WorkflowManager initialized with config: {masked_config_for_log}")

        self._active_language = self.config.get("language", "ja") # Default to Japanese if not set
        self.logger.info(f"WorkflowManager: Initial active language set to '{self._active_language}'")

        # Initialize components based on config
        self.audio_processor = AudioProcessor(logger=self.logger)
        self.asr_service = WhisperService(
            model_name=self.config.get("asr_model", "small"),
            device=self.config.get("device", "cpu"),
            logger=self.logger
        )
        
        # Initialize Normalizer and store its initial dictionary path
        initial_custom_dict_path = self.config.get("custom_dict_path")
        self.normalizer = ASRNormalizer(custom_dictionary_path=initial_custom_dict_path, logger=self.logger)
        # Initialize normalizer with current language (assuming set_language method will exist)
        if hasattr(self.normalizer, 'set_language'):
            self.normalizer.set_language(self._active_language)
        self._current_normalizer_custom_dict_path = self.normalizer.current_dictionary_path
        self.logger.info(f"WorkflowManager: Initial custom dictionary for Normalizer is '{self._current_normalizer_custom_dict_path}'")

        self.punctuator = Punctuator(language=self._active_language, logger=self.logger)
        
        # Initialize SubtitleSegmenter with timeline parameters from config
        segmenter_min_duration = self.config.get("min_duration_sec", 1.0)
        segmenter_min_gap = self.config.get("min_gap_sec", 0.1)
        # Potentially, max_chars_per_line and max_duration_sec could also come from config here
        # segmenter_max_chars = self.config.get("segmenter_max_chars_per_line", 25)
        # segmenter_max_duration = self.config.get("segmenter_max_duration_sec", 7.0)

        self.segmenter = SubtitleSegmenter(
            language=self._active_language,
            logger=self.logger,
            min_duration_sec=segmenter_min_duration,
            min_gap_sec=segmenter_min_gap
            # max_chars_per_line=segmenter_max_chars, # If these were configurable
            # max_duration_sec=segmenter_max_duration  # If these were configurable
        )
        self.logger.info(f"SubtitleSegmenter initialized with min_duration={segmenter_min_duration}s, min_gap={segmenter_min_gap}s.")
        
        self.llm_enhancer = None
        if self.config.get("llm_enabled", False):
            # API key should be loaded from config
            api_key = self.config.get("llm_api_key")
            model_name = self.config.get("llm_model_name", "gpt-3.5-turbo") # Updated to llm_model_name
            base_url_from_config = self.config.get("llm_base_url")
            
            # Ensure base_url from config is aggressively cleaned and updated back to self.config
            if isinstance(base_url_from_config, str):
                # Remove all whitespace characters, not just leading/trailing
                aggressively_cleaned_base_url = "".join(base_url_from_config.split())
                if aggressively_cleaned_base_url != base_url_from_config: # If cleaning made a change
                    self.config["llm_base_url"] = aggressively_cleaned_base_url # Update the live config dict
                    self.logger.info(f"Aggressively cleaned llm_base_url from config: '{base_url_from_config}' -> '{aggressively_cleaned_base_url}'")
                base_url = aggressively_cleaned_base_url
            else:
                base_url = None # Handles case where llm_base_url might be None or not a string

            if api_key: # Only initialize if API key is present
                self.llm_enhancer = LLMEnhancer(
                    api_key=api_key,
                    model_name=model_name,
                    base_url=base_url,
                    language=self.config.get("language", "ja"), # Pass language
                    logger=self.logger
                )
                self.logger.info(f"LLM Enhancement enabled with model: {model_name}, Base URL: {base_url if base_url else 'Default'}.")
            else:
                self.logger.warning("LLM Enhancement enabled in config, but API key is missing. LLM enhancer will not be active.")
                self.llm_enhancer = None
        else:
            self.logger.info("LLM Enhancement disabled.")

        self.formatters = {
            "srt": SRTFormatter(logger=self.logger),
            "lrc": LRCFormatter(logger=self.logger),
            "ass": ASSFormatter(logger=self.logger),
            "txt": TxtFormatter(logger=self.logger)
        }
        self.logger.info("Core components initialized based on config.")


    def process_audio_to_subtitle(self, audio_video_path: str, asr_model: str, device: str,
                                  llm_enabled: bool, llm_params: dict = None,
                                  output_format: str = "srt",
                                  current_custom_dict_path: str = None,
                                  processing_language: str = "ja",
                                  min_duration_sec: float = 1.0, # New timeline param
                                  min_gap_sec: float = 0.1       # New timeline param
                                  ) -> tuple[str, list]:
        """
        Full workflow: from audio/video input to structured subtitle data and a preview string.

        Args:
            audio_video_path (str): Path to the input audio/video file.
            asr_model (str): The ASR model to use (e.g., "small", "medium").
            device (str): The processing device ("cpu", "cuda", "mps").
            llm_enabled (bool): Whether to enable LLM enhancement.
            llm_params (dict, optional): Parameters for LLM enhancer if enabled.
            output_format (str): Desired preview output subtitle format ("srt", "lrc", "ass").
            current_custom_dict_path (str, optional): Path to the custom dictionary for this run.
            processing_language (str): Language code for this run (e.g., "ja", "zh", "en").
            min_duration_sec (float): Minimum duration for a subtitle entry for this run.
            min_gap_sec (float): Minimum gap between subtitle entries for this run.

        Returns:
            tuple[str, list]: (preview_string, structured_subtitle_data)
        """
        self.logger.info(f"开始生成字幕工作流，文件: {audio_video_path}, 语言: {processing_language}, "
                         f"ASR模型: {asr_model}, 设备: {device}, LLM启用: {llm_enabled}, "
                         f"自定义词典: {current_custom_dict_path if current_custom_dict_path else '无'}, "
                         f"最小持续: {min_duration_sec}s, 最小间隔: {min_gap_sec}s")
        if llm_enabled and llm_params:
             self.logger.info(f"LLM参数: 模型={llm_params.get('model_name')}, BaseURL配置={bool(llm_params.get('base_url'))}")

        # Dynamically update language and segmenter params if changed
        language_changed = processing_language != self._active_language
        segmenter_needs_reinit = False

        if language_changed:
            self.logger.info(f"处理语言已更改，从 '{self._active_language}' 到 '{processing_language}'. 更新下游组件。")
            if hasattr(self.punctuator, 'set_language'):
                self.punctuator.set_language(processing_language)
            else:
                self.punctuator = Punctuator(language=processing_language, logger=self.logger)
            
            if hasattr(self.normalizer, 'set_language'):
                self.normalizer.set_language(processing_language)
            
            segmenter_needs_reinit = True # Language change always triggers segmenter re-init
            self._active_language = processing_language

        # Check if segmenter's timeline parameters need updating
        # Assumes self.segmenter.min_duration_sec and self.segmenter.min_gap_sec exist
        if (not segmenter_needs_reinit and # Only check if not already flagged for re-init due to language
            (self.segmenter.min_duration_sec != min_duration_sec or
             self.segmenter.min_gap_sec != min_gap_sec)):
            self.logger.info(f"Segmenter 时间轴参数已更改。旧: min_dur={self.segmenter.min_duration_sec}, min_gap={self.segmenter.min_gap_sec}. "
                             f"新: min_dur={min_duration_sec}, min_gap={min_gap_sec}.")
            segmenter_needs_reinit = True

        if segmenter_needs_reinit:
            self.logger.info(f"重新初始化 SubtitleSegmenter。语言: {processing_language}, "
                             f"min_dur: {min_duration_sec}, min_gap: {min_gap_sec}")
            # Assume max_chars_per_line and max_duration_sec are consistent for now or taken from config
            # If they were also dynamic per run, they'd need to be passed here too.
            current_max_chars = self.segmenter.max_chars_per_line # Preserve existing max_chars
            current_max_duration = self.segmenter.max_duration_sec # Preserve existing max_duration
            self.segmenter = SubtitleSegmenter(
                language=processing_language,
                logger=self.logger,
                min_duration_sec=min_duration_sec,
                min_gap_sec=min_gap_sec,
                max_chars_per_line=current_max_chars, # Use existing or make configurable
                max_duration_sec=current_max_duration # Use existing or make configurable
            )
            # Note: LLMEnhancer takes language at init, and also dynamically if re-init.
            # Its language also needs to be updated if it exists and processing_language changed.
            if self.llm_enhancer and hasattr(self.llm_enhancer, 'set_language'):
                 self.llm_enhancer.set_language(processing_language)
            elif self.llm_enhancer: # Re-init if no set_language but LLM is active
                # This assumes llm_params would be available if llm_enhancer exists.
                # This re-init might be complex if llm_params aren't readily available here.
                # For now, relying on LLM being re-initialized later if llm_enabled and params are passed.
                # A simpler approach: LLMEnhancer's language is tied to its init based on self.config.
                # If global config language changes, WorkflowManager would need re-init for LLM.
                # OR, llm_params passed to this function should include the target language for LLM.
                # The current LLM init in this method already uses self.config.get("language", "ja")
                # Let's assume LLM is re-initialized if llm_params are provided and change.
                pass


        # Update ASR service (already done if config changes, but ensure it's set for this run's params)
        self.asr_service.update_model_and_device(model_name=asr_model, device=device)

        # Update Normalizer's custom dictionary if the path has changed
        if current_custom_dict_path != self.normalizer.current_dictionary_path:
            self.logger.info(f"自定义词典路径已更改。旧: '{self.normalizer.current_dictionary_path}', 新: '{current_custom_dict_path}'. 正在更新Normalizer。")
            self.normalizer.set_custom_dictionary_path(current_custom_dict_path)
            self._current_normalizer_custom_dict_path = self.normalizer.current_dictionary_path
        
        # Dynamically create or update LLMEnhancer instance based on current request parameters
        # LLM enhancer re-initialization if enabled and params change (this also sets its language from config)
        if llm_enabled and llm_params and llm_params.get("api_key"):
            # Ensure llm_params['base_url'] is also aggressively cleaned if it comes from UI/elsewhere directly
            current_api_key = llm_params.get("api_key")
            current_model_name = llm_params.get("model_name", "gpt-3.5-turbo")
            current_base_url_raw = llm_params.get("base_url")
            # Aggressively clean: remove all whitespace
            current_base_url = "".join(current_base_url_raw.split()) if isinstance(current_base_url_raw, str) else None

            needs_reinitialization = not self.llm_enhancer or \
                                     not self.llm_enhancer.api_key_provided or \
                                     self.llm_enhancer.model_name != current_model_name

            # Check if re-initialization is needed based on API key, model name, or base domain changes
            if self.llm_enhancer: # If an enhancer instance already exists
                # LLMEnhancer now uses self.base_domain_for_requests to store the user-provided domain
                if not self.llm_enhancer.api_key_provided or \
                   self.llm_enhancer.model_name != current_model_name or \
                   (hasattr(self.llm_enhancer, 'base_domain_for_requests') and self.llm_enhancer.base_domain_for_requests != current_base_url) or \
                   (not hasattr(self.llm_enhancer, 'base_domain_for_requests') and current_base_url is not None): # Case where old enhancer didn't have it but new one does
                    needs_reinitialization = True
            # If no LLMEnhancer exists yet, but we have params to create one
            elif current_api_key and current_model_name:
                needs_reinitialization = True


            if needs_reinitialization:
                self.logger.info(f"重新初始化/更新 LLMEnhancer. API Key: Provided, Model: {current_model_name}, Base URL: {current_base_url}")
                self.llm_enhancer = LLMEnhancer(
                    api_key=current_api_key,
                    model_name=current_model_name,
                    base_url=current_base_url, # Pass stripped version
                    language=processing_language, # Use current processing_language for LLM
                    logger=self.logger
                )
        elif not llm_enabled:
            if self.llm_enhancer:
                self.logger.info("LLM Enhancer 已禁用，正在停用。")
            self.llm_enhancer = None # Deactivate LLM enhancer

        structured_subtitle_data = []
        preview_text = ""

        # 0. Create a temporary directory for intermediate files
        with tempfile.TemporaryDirectory() as temp_dir:
            base_name = os.path.splitext(os.path.basename(audio_video_path))[0]
            processed_audio_path = os.path.join(temp_dir, f"{base_name}_processed.wav")
            
            # 1. Preprocess audio (convert, extract from video if needed, standardize)
            try:
                self.logger.info(f"正在预处理音频文件: {audio_video_path}")
                self.audio_processor.preprocess_audio(audio_video_path, processed_audio_path)
                self.logger.info(f"音频预处理完成，生成文件: {processed_audio_path}")
            except Exception as e:
                self.logger.error(f"音频预处理失败: {e}", exc_info=True)
                return f"音频预处理失败: {e}", []

            # 2. ASR Transcription
            try:
                self.logger.info(f"正在进行ASR转录 (语言: {processing_language})...")
                # transcribe returns a tuple: (segments_list, info_object)
                transcription_result_tuple = self.asr_service.transcribe(processed_audio_path, language=processing_language)
                asr_segments_list = transcription_result_tuple[0] # Extract the list of segments
                # transcription_info = transcription_result_tuple[1] # transcription_info can be used if needed

                if not asr_segments_list: # Check the actual list of segments
                    self.logger.warning("ASR未生成任何片段。")
                    return "ASR未生成任何片段。", []
                self.logger.info(f"ASR转录完成，生成 {len(asr_segments_list)} 个片段。") # Log length of the list
            except Exception as e:
                self.logger.error(f"ASR转录失败: {e}", exc_info=True)
                return f"ASR转录失败: {e}", []

            # 3. Text Normalization (e.g., custom dictionary application)
            self.logger.info("正在进行文本规范化...")
            normalized_segments = self.normalizer.normalize_text_segments(asr_segments_list) # Pass the list of segments
            self.logger.info(f"文本规范化完成，生成 {len(normalized_segments)} 个片段。")

            # 4. Punctuation
            self.logger.info("正在添加标点符号...")
            punctuated_segments = self.punctuator.add_punctuation(normalized_segments)
            self.logger.info(f"标点符号添加完成，生成 {len(punctuated_segments)} 个片段。")

            # 5. LLM Enhancement (Optional)
            # Check if llm_enhancer exists and is configured with an API key
            if llm_enabled and self.llm_enhancer and self.llm_enhancer.api_key_provided:
                self.logger.info("正在应用异步LLM增强...")
                try:
                    # asyncio.run() is suitable for calling an async function from sync code.
                    # It handles the event loop creation and teardown.
                    # This is called from a thread, so asyncio.run() will create a new event loop in this thread.
                    self.logger.info("Using asyncio.run to execute async_enhance_text_segments.")
                    enhanced_segments = asyncio.run(self.llm_enhancer.async_enhance_text_segments(punctuated_segments))
                    punctuated_segments = enhanced_segments # Update with enhanced segments
                    self.logger.info(f"异步LLM增强完成，生成 {len(punctuated_segments)} 个片段。")
                except Exception as e:
                    self.logger.error(f"异步LLM增强期间发生错误: {e}", exc_info=True)
                    self.logger.warning("LLM增强失败，将使用未增强的文本。")
            elif llm_enabled and (not self.llm_enhancer or not self.llm_enhancer.api_key_provided):
                 self.logger.warning("LLM增强已启用但LLM Enhancer未正确初始化 (缺少API Key或Base Domain)。跳过LLM增强。")

            # 6. Subtitle Segmentation (into lines/entries)
            self.logger.info("正在进行字幕分段...")
            subtitle_lines = self.segmenter.segment_into_subtitle_lines(punctuated_segments)
            if not subtitle_lines:
                self.logger.warning("字幕分段未生成任何行。")
                return "字幕分段未生成任何行。", []
            self.logger.info(f"字幕分段完成，生成 {len(subtitle_lines)} 行字幕。")
            
            # Convert List[Dict] from segmenter to List[pysrt.SubRipItem]
            pysrt_items = []
            if subtitle_lines and isinstance(subtitle_lines, list):
                for idx, dict_item in enumerate(subtitle_lines):
                    start_time_s = dict_item.get('start', 0.0)
                    end_time_s = dict_item.get('end', 0.0)
                    text = str(dict_item.get('text', ''))

                    try:
                        start_time_s = float(start_time_s)
                        end_time_s = float(end_time_s)
                    except (ValueError, TypeError):
                        self.logger.error(f"WorkflowManager: Invalid time value for item {idx} during conversion: start='{start_time_s}', end='{end_time_s}'. Skipping item.")
                        continue

                    start_obj = pysrt.SubRipTime(seconds=start_time_s)
                    end_obj = pysrt.SubRipTime(seconds=end_time_s)
                    
                    if start_obj > end_obj:
                        self.logger.warning(f"WorkflowManager data conversion: item {idx} has start > end ({start_obj} > {end_obj}). Clamping end to start.")
                        end_obj = pysrt.SubRipTime(seconds=start_time_s) # Create new object
                        
                    pysrt_items.append(pysrt.SubRipItem(
                        index=idx + 1,
                        start=start_obj,
                        end=end_obj,
                        text=text
                    ))
                structured_subtitle_data = pysrt_items
                self.logger.info(f"已将 {len(subtitle_lines)} 个字典条目转换为 {len(pysrt_items)} 个 SubRipItem 对象。")
            else:
                self.logger.warning(f"Subtitle lines from segmenter was empty or not a list: {subtitle_lines}")
                structured_subtitle_data = []

        # 7. Generate preview string using the desired output_format
        # Now structured_subtitle_data is List[pysrt.SubRipItem]
        preview_text = self.export_subtitles(structured_subtitle_data, output_format)
        self.logger.info(f"已生成 {output_format.upper()} 格式的预览。")

        return preview_text, structured_subtitle_data

    def export_subtitles(self, structured_data: list, target_format: str) -> str:
        """
        Formats structured subtitle data into a specific subtitle format string.

        Args:
            structured_data (list): A list of subtitle entry objects/dicts.
            target_format (str): The desired output format ("srt", "lrc", "ass").

        Returns:
            str: The formatted subtitle string.
        Raises:
            ValueError: If the target format is not supported.
        """
        formatter = self.formatters.get(target_format.lower())
        if not formatter:
            self.logger.error(f"不支持的字幕格式: {target_format}")
            raise ValueError(f"不支持的字幕格式: {target_format}")
        
        self.logger.info(f"正在将结构化字幕数据格式化为 {target_format.upper()}。")
        formatted_string = formatter.format_subtitles(structured_data)
        return formatted_string

    def update_config(self, new_config: dict):
        """Updates the manager's configuration and re-initializes components if necessary."""
        self.config.update(new_config)
        self.logger.info(f"WorkflowManager config updated: {self.config}")
        # Potentially re-initialize services like ASR or LLM if relevant config changed
        # This is handled dynamically in process_audio_to_subtitle for ASR/LLM
        # but could be done here if a full re-init of other components is needed.
        self.logger.info("Components would be re-initialized if necessary based on new config.")

    async def async_close_resources(self):
        """Asynchronously closes any resources held by the WorkflowManager, like the LLM enhancer's HTTP client."""
        self.logger.info("WorkflowManager: Closing resources...")
        if hasattr(self, 'llm_enhancer') and self.llm_enhancer and hasattr(self.llm_enhancer, 'close_http_client'):
            try:
                self.logger.info("WorkflowManager: Attempting to close LLM Enhancer HTTP client...")
                await self.llm_enhancer.close_http_client()
                self.logger.info("WorkflowManager: LLM Enhancer HTTP client closed.")
            except Exception as e:
                self.logger.error(f"WorkflowManager: Error closing LLM Enhancer HTTP client: {e}", exc_info=True)
        else:
            self.logger.info("WorkflowManager: No LLM Enhancer client to close or close_http_client method not found.")
        self.logger.info("WorkflowManager: Resources closed.")

    def close_resources_sync(self):
        """Synchronously closes resources. Meant to be called from non-async context like app shutdown."""
        self.logger.info("WorkflowManager: close_resources_sync called.")
        try:
            if hasattr(self, 'async_close_resources'): # Check if method exists to be safe
                # Ensure an event loop exists and run the async close method.
                # This is a simplified approach for shutdown.
                try:
                    loop = asyncio.get_event_loop_policy().get_event_loop()
                    if loop.is_running():
                        self.logger.info("WorkflowManager: Event loop is running. Creating task for async_close_resources.")
                        # This creates a task but doesn't guarantee its completion before app exit
                        # if not awaited properly or if the loop closes too soon.
                        # For a robust shutdown, a proper async shutdown sequence in the app is better.
                        loop.create_task(self.async_close_resources())
                        # Consider if we need to wait here briefly or if this is "best effort"
                    else:
                        self.logger.info("WorkflowManager: No event loop running, using asyncio.run for async_close_resources.")
                        asyncio.run(self.async_close_resources())
                except RuntimeError as e: # Handles "no event loop" type errors from get_event_loop if policy doesn't set one
                    self.logger.warning(f"WorkflowManager: Could not get event loop for async_close_resources ({e}), trying asyncio.run directly.")
                    asyncio.run(self.async_close_resources()) # Fallback
        except Exception as e:
            self.logger.error(f"WorkflowManager: Error in close_resources_sync: {e}", exc_info=True)
def parse_subtitle_string(self, subtitle_string: str, source_format: str) -> list:
        """
        Parses a subtitle string in a specific format into structured subtitle data.

        Args:
            subtitle_string (str): The subtitle content as a string.
            source_format (str): The format of the subtitle_string (e.g., "srt").

        Returns:
            list: A list of structured subtitle entry dicts.
                  Returns empty list if parsing fails.
        
        Raises:
            ValueError: If the source format is not supported or parsing not implemented.
        """
        format_key = source_format.lower()
        formatter = self.formatters.get(format_key)

        if not formatter:
            self.logger.error(f"Unsupported subtitle format for parsing: {source_format}")
            raise ValueError(f"Unsupported subtitle format for parsing: {source_format}")

        parsing_method_name = f"parse_{format_key}_string" # e.g., parse_srt_string
        
        if hasattr(formatter, parsing_method_name):
            parsing_method = getattr(formatter, parsing_method_name)
            self.logger.info(f"Parsing {source_format.upper()} string using {formatter.__class__.__name__}.{parsing_method_name}...")
            try:
                structured_data = parsing_method(subtitle_string)
                return structured_data
            except Exception as e:
                self.logger.error(f"Error parsing {source_format.upper()} string with {parsing_method_name}: {e}", exc_info=True)
                return [] # Return empty list on parsing error
        # Fallback for a generic "parse_string" method if specific one doesn't exist (less ideal)
        elif hasattr(formatter, 'parse_string'):
            self.logger.warning(f"Specific parsing method '{parsing_method_name}' not found for {source_format}. Attempting generic 'parse_string'.")
            try:
                structured_data = formatter.parse_string(subtitle_string) # type: ignore
                return structured_data
            except Exception as e:
                self.logger.error(f"Error parsing {source_format.upper()} string with generic 'parse_string': {e}", exc_info=True)
                return []
        else:
            self.logger.error(f"Formatter for {source_format} does not have a suitable parsing method ('{parsing_method_name}' or 'parse_string').")
            raise NotImplementedError(f"Parsing not implemented for {source_format} in its formatter.")
