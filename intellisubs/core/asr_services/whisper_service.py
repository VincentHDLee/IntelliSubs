# Whisper ASR Service Implementation
from .base_asr import BaseASRService
from faster_whisper import WhisperModel
import logging

class WhisperService(BaseASRService):
    def __init__(self, model_name: str = "small", device: str = "cpu", compute_type: str = "float32", logger: logging.Logger = None):
        """
        Initializes the Whisper ASR service.

        Args:
            model_name (str): Name of the Whisper model to use (e.g., "tiny", "base", "small", "medium", "large").
            device (str): Device to use for computation ("cpu", "cuda", or "mps").
            compute_type (str): Compute type for the model (e.g., "int8", "float16", "float32").
            logger (logging.Logger, optional): Logger instance.
        """
        super().__init__(logger)
        self._model = None # Private attribute for the model instance
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self._load_model()
        self.logger.info(f"WhisperService initialized with model: {model_name}, device: {device}, compute_type: {compute_type}")

    def _load_model(self):
        """Loads the Whisper model based on current settings."""
        try:
            self.logger.info(f"Loading Whisper model: {self.model_name} on {self.device} with {self.compute_type} compute type...")
            self._model = WhisperModel(self.model_name, device=self.device, compute_type=self.compute_type)
            self.logger.info("Whisper model loaded successfully.")
        except Exception as e:
            self.logger.error(f"Failed to load Whisper model {self.model_name}: {e}", exc_info=True)
            raise # Re-raise the exception to indicate a critical failure

    def transcribe(self, audio_path: str, language: str = None) -> list: # Added language parameter
        """
        Transcribes the audio file using Whisper.

        Args:
            audio_path (str): Path to the audio file.
            language (str, optional): Language code for transcription (e.g., "en", "ja", "zh").
                                      If None, faster-whisper will attempt to auto-detect the language.

        Returns:
            list: A list of segment objects or dictionaries.
                  Example segment: {'text': "some text", 'start': 0.0, 'end': 1.5}
        """
        if not self._model:
            self.logger.error("Whisper model is not loaded. Cannot transcribe.")
            raise RuntimeError("Whisper model is not loaded.")

        log_lang = language if language else "auto-detect"
        self.logger.info(f"开始转录: {audio_path} (模型: {self.model_name}, 设备: {self.device}, 语言: {log_lang})")
        
        # Pass the language parameter to faster-whisper.
        # If language is None, faster-whisper performs language detection.
        segments_generator, info = self._model.transcribe(audio_path, beam_size=5, language=language)
        
        transcribed_segments = []
        for segment in segments_generator:
            transcribed_segments.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text
            })
        self.logger.info(f"转录完成。检测语言: '{info.language}' (概率: {info.language_probability:.2f})，共 {len(transcribed_segments)} 个片段。")
        return transcribed_segments

    def update_model_and_device(self, model_name: str, device: str):
        """
        Updates the Whisper model and device. Reloads the model if settings change.
        """
        if self.model_name != model_name or self.device != device:
            self.logger.info(f"更新Whisper模型/设备：从 {self.model_name}/{self.device} 到 {model_name}/{device}")
            self.model_name = model_name
            self.device = device
            # Reload the model with new settings
            self._load_model()
        else:
            self.logger.debug("模型和设备设置未更改，无需重新加载Whisper模型。")