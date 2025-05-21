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
        self.logger.info(f"WorkflowManager initialized with config: {self.config}")

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
            # API key should be loaded from config (potentially from a secure source)
            # For now, it's expected to be in config or handled by LLMEnhancer itself
            self.llm_enhancer = LLMEnhancer(
                api_key=self.config.get("llm_api_key"), # Expect LLM_API_KEY in config
                model_name=self.config.get("llm_model", "gpt-3.5-turbo"), # Expect LLM_MODEL in config
                logger=self.logger
            )
            self.logger.info("LLM Enhancement enabled.")
        else:
            self.logger.info("LLM Enhancement disabled.")

        self.formatters = {
            "srt": SRTFormatter(logger=self.logger),
            "lrc": LRCFormatter(logger=self.logger),
            "ass": ASSFormatter(logger=self.logger),
            "txt": TxtFormatter(logger=self.logger)
        }
        self.logger.info("Core components initialized based on config.")


    def process_audio_to_subtitle(self, audio_video_path: str, asr_model: str, device: str, llm_enabled: bool, output_format: str = "srt") -> tuple[str, list]:
        """
        Full workflow: from audio/video input to structured subtitle data and a preview string.

        Args:
            audio_video_path (str): Path to the input audio/video file.
            asr_model (str): The ASR model to use (e.g., "small", "medium").
            device (str): The processing device ("cpu", "cuda", "mps").
            llm_enabled (bool): Whether to enable LLM enhancement.
            output_format (str): Desired preview output subtitle format ("srt", "lrc", "ass").

        Returns:
            tuple[str, list]: (preview_string, structured_subtitle_data)
                             structured_subtitle_data is a list of dicts/objects representing subtitle entries.
        """
        self.logger.info(f"开始生成字幕工作流，文件: {audio_video_path}, 模型: {asr_model}, 设备: {device}, LLM: {llm_enabled}")

        # Update ASR service and LLM enhancer if settings changed
        self.asr_service.update_model_and_device(model_name=asr_model, device=device)
        
        if llm_enabled and not self.llm_enhancer:
            self.llm_enhancer = LLMEnhancer(
                api_key=self.config.get("llm_api_key"),
                model_name=self.config.get("llm_model", "gpt-3.5-turbo"),
                logger=self.logger
            )
            self.logger.info("LLM Enhancer activated dynamically.")
        elif not llm_enabled and self.llm_enhancer:
            self.llm_enhancer = None # Deactivate LLM enhancer
            self.logger.info("LLM Enhancer deactivated dynamically.")

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
            if self.llm_enhancer:
                self.logger.info("正在应用LLM增强...")
                punctuated_segments = self.llm_enhancer.enhance_text_segments(punctuated_segments)
                self.logger.info(f"LLM增强完成，生成 {len(punctuated_segments)} 个片段。")
            
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

    def update_config(self, new_config: dict):
        """Updates the manager's configuration and re-initializes components if necessary."""
        self.config.update(new_config)
        print(f"WorkflowManager config updated: {self.config}")
        # Potentially re-initialize services like ASR or LLM if relevant config changed
        # e.g., if self.config.get("asr_model") changed, re-init self.asr_service
        print("Components would be re-initialized if necessary based on new config.")