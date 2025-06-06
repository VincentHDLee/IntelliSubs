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
import asyncio
from intellisubs.utils.logger_setup import mask_sensitive_data
import pysrt

class WorkflowManager:
    def __init__(self, config: dict = None, logger: logging.Logger = None):
        self.config = config if config else {}
        self.logger = logger if logger else logging.getLogger(__name__)
        masked_config_for_log = mask_sensitive_data(self.config)
        self.logger.info(f"WorkflowManager initialized with config: {masked_config_for_log}")

        self._active_language = self.config.get("language", "ja")
        self.logger.info(f"WorkflowManager: Initial active language set to '{self._active_language}'")
        self.available_llm_models = []

        self.audio_processor = AudioProcessor(logger=self.logger)
        self.asr_service = WhisperService(
            model_name=self.config.get("asr_model", "small"),
            device=self.config.get("device", "cpu"),
            logger=self.logger
        )
        
        initial_custom_dict_path = self.config.get("custom_dict_path")
        self.normalizer = ASRNormalizer(custom_dictionary_path=initial_custom_dict_path, logger=self.logger)
        if hasattr(self.normalizer, 'set_language'):
            self.normalizer.set_language(self._active_language)
        self._current_normalizer_custom_dict_path = self.normalizer.current_dictionary_path
        self.logger.info(f"WorkflowManager: Initial custom dictionary for Normalizer is '{self._current_normalizer_custom_dict_path}'")

        self.punctuator = Punctuator(language=self._active_language, logger=self.logger)
        
        segmenter_min_duration = self.config.get("min_duration_sec", 1.0)
        segmenter_min_gap = self.config.get("min_gap_sec", 0.1)
        self.segmenter = SubtitleSegmenter(
            language=self._active_language,
            logger=self.logger,
            min_duration_sec=segmenter_min_duration,
            min_gap_sec=segmenter_min_gap
        )
        self.logger.info(f"SubtitleSegmenter initialized with min_duration={segmenter_min_duration}s, min_gap={segmenter_min_gap}s.")
        
        self.llm_enhancer = None
        if self.config.get("llm_enabled", False):
            api_key = self.config.get("llm_api_key")
            model_name = self.config.get("llm_model_name", "gpt-3.5-turbo")
            base_url_from_config = self.config.get("llm_base_url") # Use single base_url
            
            # Basic cleaning (strip), LLMEnhancer will also strip and rstrip('/')
            cleaned_base_url = base_url_from_config.strip() if isinstance(base_url_from_config, str) else None
            
            if api_key:
                self.llm_enhancer = LLMEnhancer(
                    api_key=api_key,
                    model_name=model_name,
                    base_url=cleaned_base_url,
                    language=self.config.get("language", "ja"),
                    logger=self.logger,
                    # script_context is handled dynamically
                    user_override_system_prompt=self.config.get("llm_system_prompt"), # User override from global config
                    config_prompts=self.config.get("llm_prompts") # Default prompts from global config
                )
                self.logger.info(f"LLM Enhancement enabled. Model: {model_name}, Base URL: {cleaned_base_url if cleaned_base_url else 'Default'}.")
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

    def set_language(self, language_code: str):
        """
        Sets the active language for the WorkflowManager and its components.
        """
        if language_code == self._active_language:
            self.logger.debug(f"WorkflowManager.set_language: Language '{language_code}' is already active. No change needed.")
            return

        self.logger.info(f"WorkflowManager.set_language: Changing active language from '{self._active_language}' to '{language_code}'.")
        self._active_language = language_code

        if hasattr(self.punctuator, 'set_language'):
            self.punctuator.set_language(language_code)
            self.logger.debug(f"Punctuator language set to '{language_code}'.")
        else:
            self.logger.warning("Punctuator does not have set_language, re-initializing.")
            self.punctuator = Punctuator(language=language_code, logger=self.logger)

        if hasattr(self.normalizer, 'set_language'):
            self.normalizer.set_language(language_code)
            self.logger.debug(f"Normalizer language set to '{language_code}'.")
        
        # Re-initialize segmenter as its internal state might depend on language (e.g., punctuation rules)
        # and it doesn't have a standalone set_language in the current snippet from process_audio_to_subtitle
        # We'll keep its existing time parameters.
        current_min_dur = self.segmenter.min_duration_sec
        current_min_gap = self.segmenter.min_gap_sec
        current_max_chars = self.segmenter.max_chars_per_line
        current_max_duration = self.segmenter.max_duration_sec
        self.logger.info(f"Re-initializing SubtitleSegmenter due to language change to '{language_code}'. "
                         f"Keeping time params: min_dur={current_min_dur}, min_gap={current_min_gap}, "
                         f"max_chars={current_max_chars}, max_dur={current_max_duration}")
        self.segmenter = SubtitleSegmenter(
            language=language_code,
            logger=self.logger,
            min_duration_sec=current_min_dur,
            min_gap_sec=current_min_gap,
            max_chars_per_line=current_max_chars,
            max_duration_sec=current_max_duration
        )

        if self.llm_enhancer and hasattr(self.llm_enhancer, 'set_language'):
            self.llm_enhancer.set_language(language_code)
            self.logger.debug(f"LLMEnhancer language set to '{language_code}'.")
        
        self.logger.info(f"WorkflowManager active language and components updated to '{language_code}'.")

    def set_custom_dictionary(self, dictionary_path: str, language_code: str = None): # language_code might be for future use or context
        """
        Sets the custom dictionary for the ASRNormalizer.
        Args:
            dictionary_path (str): Path to the custom dictionary file.
            language_code (str, optional): Language code, currently not directly used by normalizer.set_custom_dictionary_path
                                           but included for potential future consistency or logging.
        """
        # The language_code argument is not directly used by normalizer.set_custom_dictionary_path
        # but it's good practice if other components related to dictionary might need it.
        # For now, we primarily focus on the path.
        
        # We should compare with the Normalizer's current path to avoid redundant calls if possible,
        # similar to the logic in process_audio_to_subtitle.
        if dictionary_path == self.normalizer.current_dictionary_path:
            self.logger.debug(f"WorkflowManager.set_custom_dictionary: Dictionary path '{dictionary_path}' is already active in Normalizer. No change needed.")
            return

        self.logger.info(f"WorkflowManager.set_custom_dictionary: Setting custom dictionary path to '{dictionary_path}' for Normalizer.")
        if hasattr(self.normalizer, 'set_custom_dictionary_path'):
            self.normalizer.set_custom_dictionary_path(dictionary_path)
            # Update the WorkflowManager's tracking variable if it exists, like _current_normalizer_custom_dict_path
            self._current_normalizer_custom_dict_path = self.normalizer.current_dictionary_path
            self.logger.info(f"Normalizer custom dictionary path updated to '{self.normalizer.current_dictionary_path}'.")
        else:
            self.logger.error("WorkflowManager.set_custom_dictionary: Normalizer does not have 'set_custom_dictionary_path' method.")

    def update_processing_parameters(self, min_duration_sec: float = None, min_gap_sec: float = None):
        """
        Updates processing parameters, currently focused on SubtitleSegmenter's time settings.
        Args:
            min_duration_sec (float, optional): New minimum duration for subtitle segments.
            min_gap_sec (float, optional): New minimum gap between subtitle segments.
        """
        needs_segmenter_reinit = False
        
        current_segmenter_min_dur = self.segmenter.min_duration_sec
        current_segmenter_min_gap = self.segmenter.min_gap_sec

        # Check if min_duration_sec needs update
        if min_duration_sec is not None and min_duration_sec != current_segmenter_min_dur:
            self.logger.info(f"WorkflowManager: min_duration_sec will be updated from {current_segmenter_min_dur} to {min_duration_sec}.")
            current_segmenter_min_dur = min_duration_sec
            needs_segmenter_reinit = True
        
        # Check if min_gap_sec needs update
        if min_gap_sec is not None and min_gap_sec != current_segmenter_min_gap:
            self.logger.info(f"WorkflowManager: min_gap_sec will be updated from {current_segmenter_min_gap} to {min_gap_sec}.")
            current_segmenter_min_gap = min_gap_sec
            needs_segmenter_reinit = True

        if needs_segmenter_reinit:
            self.logger.info(f"Re-initializing SubtitleSegmenter due to parameter change. "
                             f"Language: {self._active_language}, "
                             f"New min_dur: {current_segmenter_min_dur}, New min_gap: {current_segmenter_min_gap}")
            
            # Preserve other existing parameters of the segmenter
            current_max_chars = self.segmenter.max_chars_per_line
            current_max_duration = self.segmenter.max_duration_sec
            
            self.segmenter = SubtitleSegmenter(
                language=self._active_language, # Use the manager's current active language
                logger=self.logger,
                min_duration_sec=current_segmenter_min_dur,
                min_gap_sec=current_segmenter_min_gap,
                max_chars_per_line=current_max_chars,
                max_duration_sec=current_max_duration
            )
            self.logger.info("SubtitleSegmenter re-initialized with new time parameters.")
        else:
            self.logger.debug("WorkflowManager.update_processing_parameters: No changes to segmenter time parameters needed.")

    def process_audio_to_subtitle(self, audio_video_path: str, asr_model: str, device: str,
                                  llm_enabled: bool, llm_params: dict = None,
                                  output_format: str = "srt",
                                  current_custom_dict_path: str = None,
                                  processing_language: str = "ja",
                                  min_duration_sec: float = 1.0,
                                  min_gap_sec: float = 0.1,
                                  llm_script_context: str = None  # New parameter
                                  ) -> tuple[str, list]:
        """
        Full workflow: from audio/video input to structured subtitle data and a preview string.
        Args:
            audio_video_path (str): Path to the input audio/video file.
            asr_model (str): The ASR model to use (e.g., "small", "medium").
            device (str): The processing device ("cpu", "cuda", "mps").
            llm_enabled (bool): Whether to enable LLM enhancement.
            llm_params (dict, optional): Parameters for LLM enhancer if enabled.
                                         Should include 'api_key', 'model_name', 'base_url', 'system_prompt'.
            output_format (str): Desired preview output subtitle format ("srt", "lrc", "ass").
            current_custom_dict_path (str, optional): Path to the custom dictionary for this run.
            processing_language (str): Language code for this run (e.g., "ja", "zh", "en").
            min_duration_sec (float): Minimum duration for a subtitle entry for this run.
            min_gap_sec (float): Minimum gap between subtitle entries for this run.
            llm_script_context (str, optional): Full text content of the imported script.
        Returns:
            tuple[str, list]: (preview_string, structured_subtitle_data)
        """
        self.logger.info(f"开始生成字幕工作流，文件: {audio_video_path}, 语言: {processing_language}, "
                         f"ASR模型: {asr_model}, 设备: {device}, LLM启用: {llm_enabled}, "
                         f"自定义词典: {current_custom_dict_path if current_custom_dict_path else '无'}, "
                         f"最小持续: {min_duration_sec}s, 最小间隔: {min_gap_sec}s, "
                         f"剧本上下文提供: {bool(llm_script_context)}")
        
        if llm_enabled and llm_params:
             self.logger.info(f"LLM参数: 模型={llm_params.get('model_name')}, BaseURL配置={bool(llm_params.get('base_url'))}, "
                              f"剧本上下文长度: {len(llm_script_context) if llm_script_context else 0}")

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
            
            segmenter_needs_reinit = True 
            self._active_language = processing_language

        if (not segmenter_needs_reinit and
            (self.segmenter.min_duration_sec != min_duration_sec or
             self.segmenter.min_gap_sec != min_gap_sec)):
            self.logger.info(f"Segmenter 时间轴参数已更改。旧: min_dur={self.segmenter.min_duration_sec}, min_gap={self.segmenter.min_gap_sec}. "
                             f"新: min_dur={min_duration_sec}, min_gap={min_gap_sec}.")
            segmenter_needs_reinit = True

        if segmenter_needs_reinit:
            self.logger.info(f"重新初始化 SubtitleSegmenter。语言: {processing_language}, "
                             f"min_dur: {min_duration_sec}, min_gap: {min_gap_sec}")
            current_max_chars = self.segmenter.max_chars_per_line
            current_max_duration = self.segmenter.max_duration_sec
            self.segmenter = SubtitleSegmenter(
                language=processing_language,
                logger=self.logger,
                min_duration_sec=min_duration_sec,
                min_gap_sec=min_gap_sec,
                max_chars_per_line=current_max_chars,
                max_duration_sec=current_max_duration
            )
            if self.llm_enhancer and hasattr(self.llm_enhancer, 'set_language'):
                 self.llm_enhancer.set_language(processing_language)

        self.asr_service.update_model_and_device(model_name=asr_model, device=device)

        if current_custom_dict_path != self.normalizer.current_dictionary_path:
            self.logger.info(f"自定义词典路径已更改。旧: '{self.normalizer.current_dictionary_path}', 新: '{current_custom_dict_path}'. 正在更新Normalizer。")
            self.normalizer.set_custom_dictionary_path(current_custom_dict_path)
            self._current_normalizer_custom_dict_path = self.normalizer.current_dictionary_path
        
        if llm_enabled and llm_params and llm_params.get("api_key"):
            current_api_key = llm_params.get("api_key")
            current_model_name = llm_params.get("model_name", "gpt-3.5-turbo")
            current_base_url_raw = llm_params.get("base_url") # Use single base_url
            current_base_url = current_base_url_raw.strip() if isinstance(current_base_url_raw, str) else None
            current_system_prompt = llm_params.get("system_prompt", "")
            
            needs_llm_reinitialization_or_update = False
            if not self.llm_enhancer:
                needs_llm_reinitialization_or_update = True
                self.logger.info("LLMEnhancer not initialized, will create new instance.")
            else:
                if (getattr(self.llm_enhancer, 'api_key', None) != current_api_key or
                    self.llm_enhancer.model_name != current_model_name or
                    getattr(self.llm_enhancer, 'base_url', None) != current_base_url or # Check base_url
                    getattr(self.llm_enhancer, 'script_context', None) != llm_script_context or
                    getattr(self.llm_enhancer, 'system_prompt', None) != current_system_prompt or
                    getattr(self.llm_enhancer, 'language', self._active_language) != processing_language):
                    needs_llm_reinitialization_or_update = True
                    self.logger.info("LLMEnhancer parameters changed, will update/re-initialize.")
            
            if needs_llm_reinitialization_or_update:
                self.logger.info(f"Initializing/Updating LLMEnhancer. API Key: Provided, Model: {current_model_name}, Base URL: {current_base_url}, Lang: {processing_language}, ScriptContext: {bool(llm_script_context)}, SystemPrompt: {bool(current_system_prompt)}")
                self.llm_enhancer = LLMEnhancer(
                    api_key=current_api_key,
                    model_name=current_model_name,
                    base_url=current_base_url,
                    language=processing_language,
                    logger=self.logger,
                    script_context=llm_script_context,
                    user_override_system_prompt=current_system_prompt, # This is the UI override
                    config_prompts=self.config.get("llm_prompts") # Default prompts from global config
                )
        elif not llm_enabled:
            if self.llm_enhancer:
                self.logger.info("LLM Enhancer 已禁用，正在停用。")
            self.llm_enhancer = None

        structured_subtitle_data = []
        preview_text = ""

        with tempfile.TemporaryDirectory() as temp_dir:
            base_name = os.path.splitext(os.path.basename(audio_video_path))[0]
            processed_audio_path = os.path.join(temp_dir, f"{base_name}_processed.wav")
            
            try:
                self.logger.info(f"正在预处理音频文件: {audio_video_path}")
                self.audio_processor.preprocess_audio(audio_video_path, processed_audio_path)
                self.logger.info(f"音频预处理完成，生成文件: {processed_audio_path}")
            except Exception as e:
                self.logger.error(f"音频预处理失败: {e}", exc_info=True)
                return f"音频预处理失败: {e}", []

            try:
                self.logger.info(f"正在进行ASR转录 (语言: {processing_language})...")
                transcription_result_tuple = self.asr_service.transcribe(processed_audio_path, language=processing_language)
                asr_segments_list = transcription_result_tuple[0]
                
                if not asr_segments_list:
                    self.logger.warning("ASR未生成任何片段。")
                    return "ASR未生成任何片段。", []

                # --- BEGIN ADDED CODE FOR ASR DUPLICATION FIX ---
                fixed_asr_segments = []
                self.logger.debug(f"ASR去重: 开始处理 {len(asr_segments_list)} 个原始片段。")
                for seg_idx, asr_seg in enumerate(asr_segments_list):
                    original_text = asr_seg.get("text", "")
                    self.logger.debug(f"ASR去重: 片段 {seg_idx} 原始内容: '{original_text}'")
                    text_to_process = original_text.strip()
                    self.logger.debug(f"ASR去重: 片段 {seg_idx} strip后内容: '{text_to_process}'")
                    corrected_text = text_to_process # Default to original stripped text
                    found_fix = False

                    # 1. Attempt to fix "A<delim>A" style duplication (e.g., "text.text", "text?text")
                    possible_delimiters_for_fix = ["。", "？", "！", ".", "?", "!", " "]
                    self.logger.debug(f"ASR去重: 片段 {seg_idx} 使用分隔符列表: {possible_delimiters_for_fix}")
                    
                    for delim_char in possible_delimiters_for_fix:
                        self.logger.debug(f"ASR去重: 片段 {seg_idx} 尝试分隔符 '{delim_char}'")
                        if delim_char and delim_char in text_to_process:
                            parts = text_to_process.split(delim_char, 1)
                            self.logger.debug(f"ASR去重: 片段 {seg_idx} 使用 '{delim_char}' 分割结果: {parts}")
                            if len(parts) == 2:
                                s1 = parts[0].strip()
                                s2 = parts[1].strip()
                                self.logger.debug(f"ASR去重: 片段 {seg_idx} s1='{s1}', s2='{s2}'")
                                if s1 and s1 == s2:
                                    corrected_text = s1 if delim_char == " " else s1 + delim_char
                                    self.logger.info(f"ASR 文本修复 (模式 '{delim_char}'): 片段 {seg_idx} 从 '{original_text}' 修复为 '{corrected_text}'")
                                    found_fix = True
                                    break
                            else:
                                self.logger.debug(f"ASR去重: 片段 {seg_idx} 使用 '{delim_char}' 分割部分不足2。")
                        else:
                            self.logger.debug(f"ASR去重: 片段 {seg_idx} 分隔符 '{delim_char}' 不存在或为空。")
                    
                    if not found_fix:
                        self.logger.debug(f"ASR去重: 片段 {seg_idx} 未通过分隔符模式修复。尝试对半模式。")
                        text_len = len(text_to_process)
                        if text_len > 2 and text_len % 2 == 0:
                            mid_point = text_len // 2
                            part1 = text_to_process[:mid_point] # .strip() is not needed here if text_to_process is already stripped
                            part2 = text_to_process[mid_point:] # .strip() is not needed here
                            self.logger.debug(f"ASR去重: 片段 {seg_idx} 对半模式: part1='{part1}', part2='{part2}'")
                            if part1 == part2 and part1:
                                corrected_text = part1
                                self.logger.info(f"ASR 文本修复 (直接对半模式): 片段 {seg_idx} 从 '{original_text}' 修复为 '{corrected_text}'")
                                # found_fix = True # Not strictly needed
                            else:
                                self.logger.debug(f"ASR去重: 片段 {seg_idx} 对半模式不匹配或part1为空。")
                        else:
                            self.logger.debug(f"ASR去重: 片段 {seg_idx} 文本长度 ({text_len}) 不适用于对半模式。")
                    
                    new_seg = asr_seg.copy()
                    new_seg["text"] = corrected_text
                    fixed_asr_segments.append(new_seg)
                    self.logger.debug(f"ASR去重: 片段 {seg_idx} 最终修正文本: '{corrected_text}', 添加到修复列表。")

                asr_segments_list = fixed_asr_segments
                # --- END ADDED CODE FOR ASR DUPLICATION FIX ---

                # --- BEGIN ADDED CODE FOR INTER-SEGMENT DUPLICATION FIX ---
                if len(asr_segments_list) > 1:
                    self.logger.debug(f"合并前，ASR片段数量: {len(asr_segments_list)}")
                    merged_asr_segments = []
                    
                    # 第一个片段直接添加
                    if asr_segments_list:
                         merged_asr_segments.append(asr_segments_list[0])

                    for i in range(1, len(asr_segments_list)):
                        current_seg = asr_segments_list[i]
                        prev_merged_seg = merged_asr_segments[-1]

                        # 条件：文本相同，且时间上基本连续 (允许小的间隙，比如0.1秒)
                        # 我们也需要考虑 prev_merged_seg['text'] 可能为空的情况
                        if prev_merged_seg.get("text") and \
                           current_seg.get("text") == prev_merged_seg.get("text") and \
                           current_seg.get("start", 0) - prev_merged_seg.get("end", -1) <= 0.2: # 允许0.2秒的间隙
                            
                            self.logger.info(f"检测到连续的相同文本片段，将合并: '{current_seg.get('text')}' "
                                             f"({prev_merged_seg.get('start'):.2f}-{prev_merged_seg.get('end'):.2f} "
                                             f"和 {current_seg.get('start'):.2f}-{current_seg.get('end'):.2f})")
                            # 扩展前一个片段的结束时间
                            prev_merged_seg["end"] = max(prev_merged_seg.get("end",0), current_seg.get("end",0))
                            self.logger.debug(f"合并后，前一片段更新为: {prev_merged_seg.get('start'):.2f}-{prev_merged_seg.get('end'):.2f}")
                        else:
                            merged_asr_segments.append(current_seg)
                    
                    if len(merged_asr_segments) < len(asr_segments_list):
                        self.logger.info(f"跨片段合并完成。片段数从 {len(asr_segments_list)} 减少到 {len(merged_asr_segments)}。")
                    asr_segments_list = merged_asr_segments
                # --- END ADDED CODE FOR INTER-SEGMENT DUPLICATION FIX ---
                
                self.logger.info(f"ASR转录完成 (应用修复和合并后)，生成 {len(asr_segments_list)} 个片段。")
            except Exception as e:
                self.logger.error(f"ASR转录失败: {e}", exc_info=True)
                return f"ASR转录失败: {e}", []

            self.logger.info("正在进行文本规范化...")
            normalized_segments = self.normalizer.normalize_text_segments(asr_segments_list)
            self.logger.info(f"文本规范化完成，生成 {len(normalized_segments)} 个片段。")

            self.logger.info("正在添加标点符号...")
            punctuated_segments = self.punctuator.add_punctuation(normalized_segments)
            self.logger.info(f"标点符号添加完成，生成 {len(punctuated_segments)} 个片段。")

            # LLM enhancement is now decoupled from this initial processing workflow.
            # The self.llm_enhancer instance is prepared if llm_enabled was true,
            # but the actual enhancement will be triggered войска UI action later.
            self.logger.info("LLM增强已解耦，不会在此阶段自动执行。")

            self.logger.info("正在进行字幕分段...")
            subtitle_lines = self.segmenter.segment_into_subtitle_lines(punctuated_segments)
            if not subtitle_lines:
                self.logger.warning("字幕分段未生成任何行。")
                return "字幕分段未生成任何行。", []
            self.logger.info(f"字幕分段完成，生成 {len(subtitle_lines)} 行字幕。")
            
            pysrt_items = []
            if subtitle_lines and isinstance(subtitle_lines, list):
                for idx, dict_item in enumerate(subtitle_lines):
                    start_time_s = dict_item.get('start', 0.0)
                    end_time_s = dict_item.get('end', 0.0)
                    text_content = str(dict_item.get('text', ''))
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
                        end_obj = pysrt.SubRipTime(seconds=start_time_s)
                    pysrt_items.append(pysrt.SubRipItem(
                        index=idx + 1, start=start_obj, end=end_obj, text=text_content
                    ))
                structured_subtitle_data = pysrt_items
                self.logger.info(f"已将 {len(subtitle_lines)} 个字典条目转换为 {len(pysrt_items)} 个 SubRipItem 对象。")
            else:
                self.logger.warning(f"Subtitle lines from segmenter was empty or not a list: {subtitle_lines}")
                structured_subtitle_data = []

        preview_text = self.export_subtitles(structured_subtitle_data, output_format)
        self.logger.info(f"已生成 {output_format.upper()} 格式的预览。")

        return preview_text, structured_subtitle_data

    def export_subtitles(self, structured_data: list, target_format: str) -> str:
        formatter = self.formatters.get(target_format.lower())
        if not formatter:
            self.logger.error(f"不支持的字幕格式: {target_format}")
            raise ValueError(f"不支持的字幕格式: {target_format}")
        
        self.logger.info(f"正在将结构化字幕数据格式化为 {target_format.upper()}。")
        formatted_string = formatter.format_subtitles(structured_data)
        return formatted_string

    def update_config(self, new_config: dict):
        self.config.update(new_config)
        self.logger.info(f"WorkflowManager config updated: {mask_sensitive_data(self.config)}") # Mask sensitive data
        self.logger.info("Components would be re-initialized if necessary based on new config.")

    async def async_get_llm_models(self, current_llm_config: dict = None) -> list[str]:
        config_to_use = current_llm_config if current_llm_config else self.config
        
        base_url = config_to_use.get("llm_base_url") # Use single base_url
        api_key = config_to_use.get("llm_api_key")
        language = config_to_use.get("language", self._active_language)

        if not base_url:
            self.logger.warning("Cannot fetch LLM models: llm_base_url is not configured.")
            self.available_llm_models = []
            return []

        # LLMEnhancer constructor will strip base_url
        
        temp_enhancer = LLMEnhancer(
            api_key=api_key if api_key else "",
            model_name="",  # Not needed for listing models
            base_url=base_url,
            language=language,
            logger=self.logger,
            user_override_system_prompt=config_to_use.get("llm_system_prompt"), # Pass user override if available in config_to_use
            config_prompts=config_to_use.get("llm_prompts") # Pass default prompts if available
        )
        
        self.logger.info(f"Attempting to fetch LLM models using base_url: {base_url} (will append /v1/models)")
        try:
            models = await temp_enhancer.async_get_available_models()
            self.available_llm_models = models
            if models:
                self.logger.info(f"Successfully fetched {len(models)} LLM models from base_url: {base_url}.")
            else:
                self.logger.warning(f"No LLM models fetched from base_url: {base_url}. The list is empty.")
            return models
        except Exception as e:
            self.logger.error(f"Error fetching LLM models: {e}", exc_info=True)
            self.available_llm_models = []
            return []
        finally: # Ensure HTTP client in temp_enhancer is closed
            if temp_enhancer:
                await temp_enhancer.close_http_client()


    async def async_close_resources(self):
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
        self.logger.info("WorkflowManager: close_resources_sync called.")
        try:
            if hasattr(self, 'async_close_resources'):
                try:
                    loop = asyncio.get_event_loop_policy().get_event_loop()
                    if loop.is_running():
                        self.logger.info("WorkflowManager: Event loop is running. Creating task for async_close_resources.")
                        loop.create_task(self.async_close_resources())
                    else:
                        self.logger.info("WorkflowManager: No event loop running, using asyncio.run for async_close_resources.")
                        asyncio.run(self.async_close_resources())
                except RuntimeError as e: 
                    self.logger.warning(f"WorkflowManager: Could not get event loop for async_close_resources ({e}), trying asyncio.run directly.")
                    asyncio.run(self.async_close_resources())
        except Exception as e:
            self.logger.error(f"WorkflowManager: Error in close_resources_sync: {e}", exc_info=True)

    def parse_subtitle_string(self, subtitle_string: str, source_format: str) -> list:
        format_key = source_format.lower()
        formatter = self.formatters.get(format_key)

        if not formatter:
            self.logger.error(f"Unsupported subtitle format for parsing: {source_format}")
            raise ValueError(f"Unsupported subtitle format for parsing: {source_format}")

        parsing_method_name = f"parse_{format_key}_string"
        
        if hasattr(formatter, parsing_method_name):
            parsing_method = getattr(formatter, parsing_method_name)
            self.logger.info(f"Parsing {source_format.upper()} string using {formatter.__class__.__name__}.{parsing_method_name}...")
            try:
                structured_data = parsing_method(subtitle_string)
                return structured_data
            except Exception as e:
                self.logger.error(f"Error parsing {source_format.upper()} string with {parsing_method_name}: {e}", exc_info=True)
                return []
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

    async def test_llm_connection_async(self, current_llm_config: dict) -> tuple[bool, str]:
        """
        Tests the LLM connection by attempting a simple chat completion.
        Args:
            current_llm_config (dict): Dictionary containing 'llm_api_key',
                                       'llm_base_url'. It may optionally include 'llm_model_name'.
        Returns:
            tuple[bool, str]: (success_status, message)
        """
        self.logger.info("WorkflowManager: Initiating LLM connection test (chat completion).")
        if not current_llm_config:
            self.logger.warning("LLM test_connection: current_llm_config is None.")
            return False, "LLM 配置信息缺失。"

        base_url = current_llm_config.get("llm_base_url")
        api_key = current_llm_config.get("llm_api_key")
        
        # Get model_name: from current_llm_config -> self.config -> default
        model_name_for_test = current_llm_config.get("llm_model_name")
        if not model_name_for_test:
            model_name_for_test = self.config.get("llm_model_name") # Check global config
        if not model_name_for_test: # Fallback to a common default if still not found
             model_name_for_test = "gpt-3.5-turbo"
             self.logger.info(f"LLM test_connection: llm_model_name not in current_llm_config or self.config, using default '{model_name_for_test}' for test.")


        if not api_key: # API key is essential for chat completion test
            self.logger.warning("LLM test_connection: API Key not provided.")
            return False, "LLM API Key 未配置。"
            
        if not base_url:
            self.logger.warning("LLM test_connection: Base URL not provided.")
            return False, "LLM Base URL 未配置。"

        self.logger.info(f"LLM test_connection: Attempting chat completion using Base URL: {base_url}, Model: {model_name_for_test}.")
        
        temp_enhancer = LLMEnhancer(
            api_key=api_key,
            model_name=model_name_for_test,
            base_url=base_url,
            language=self._active_language,
            logger=self.logger,
            # For test, use global config's user override and default prompts
            user_override_system_prompt=self.config.get("llm_system_prompt"),
            config_prompts=self.config.get("llm_prompts")
        )

        try:
            # Call the new chat completion test method in LLMEnhancer
            success, message = await temp_enhancer.async_test_chat_completion()
            
            if success:
                self.logger.info(f"LLM chat test successful via WorkflowManager: {message}")
            else:
                self.logger.warning(f"LLM chat test failed via WorkflowManager: {message}")
            return success, message # Return the direct result from the enhancer's test
            
        except Exception as e:
            self.logger.error(f"LLM test_connection: Unexpected error during chat completion test (Base URL: {base_url}, Model: {model_name_for_test}): {e}", exc_info=True)
            return False, f"测试聊天连接时发生意外错误: {e}"
        finally:
            if temp_enhancer:
                await temp_enhancer.close_http_client()
