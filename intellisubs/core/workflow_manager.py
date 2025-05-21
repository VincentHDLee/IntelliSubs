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
from intellisubs.utils.logger_setup import mask_sensitive_data # Import the masking function

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

        # Initialize components based on config
        self.audio_processor = AudioProcessor(logger=self.logger)
        self.asr_service = WhisperService(
            model_name=self.config.get("asr_model", "small"),
            device=self.config.get("device", "cpu"),
            logger=self.logger
        )
        self.normalizer = ASRNormalizer(
            custom_dictionary_path=self.config.get("custom_dict_path", "resources/custom_dictionaries/jp_custom_dict_example.csv"),
            logger=self.logger
        )
        self.punctuator = Punctuator(language="ja", logger=self.logger)
        self.segmenter = SubtitleSegmenter(language="ja", logger=self.logger)
        
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


    def process_audio_to_subtitle(self, audio_video_path: str, asr_model: str, device: str, llm_enabled: bool, llm_params: dict = None, output_format: str = "srt") -> tuple[str, list]:
        """
        Full workflow: from audio/video input to structured subtitle data and a preview string.

        Args:
            audio_video_path (str): Path to the input audio/video file.
            asr_model (str): The ASR model to use (e.g., "small", "medium").
            device (str): The processing device ("cpu", "cuda", "mps").
            llm_enabled (bool): Whether to enable LLM enhancement.
            llm_params (dict, optional): Parameters for LLM enhancer if enabled.
                                         Expected keys: "api_key", "base_url", "model_name".
            output_format (str): Desired preview output subtitle format ("srt", "lrc", "ass").

        Returns:
            tuple[str, list]: (preview_string, structured_subtitle_data)
                             structured_subtitle_data is a list of dicts/objects representing subtitle entries.
        """
        self.logger.info(f"开始生成字幕工作流，文件: {audio_video_path}, ASR模型: {asr_model}, 设备: {device}, LLM启用: {llm_enabled}")
        if llm_enabled and llm_params:
             self.logger.info(f"LLM参数: 模型={llm_params.get('model_name')}, BaseURL配置={bool(llm_params.get('base_url'))}")


        # Update ASR service
        self.asr_service.update_model_and_device(model_name=asr_model, device=device)
        
        # Dynamically create or update LLMEnhancer instance based on current request parameters
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
                    language=self.config.get("language", "ja"),
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
                self.logger.info(f"正在进行ASR转录...")
                asr_segments = self.asr_service.transcribe(processed_audio_path)
                if not asr_segments:
                    self.logger.warning("ASR未生成任何片段。")
                    return "ASR未生成任何片段。", []
                self.logger.info(f"ASR转录完成，生成 {len(asr_segments)} 个片段。")
            except Exception as e:
                self.logger.error(f"ASR转录失败: {e}", exc_info=True)
                return f"ASR转录失败: {e}", []

            # 3. Text Normalization (e.g., custom dictionary application)
            self.logger.info("正在进行文本规范化...")
            normalized_segments = self.normalizer.normalize_text_segments(asr_segments)
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
            structured_subtitle_data = subtitle_lines # This is our structured data

        # 7. Generate preview string using the desired output_format
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
