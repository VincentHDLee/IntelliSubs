# Base class for ASR services
from abc import ABC, abstractmethod
import logging

class BaseASRService(ABC):
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger if logger else logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def transcribe(self, audio_path: str) -> list:
        """
        转录给定的音频文件。

        Args:
            audio_path (str): 音频文件的路径。

        Returns:
            list: 转录的片段列表，每个片段是一个字典
                  (例如, `{"text": "...", "start": 0.0, "end": 1.0}`)。
        """
        pass

    @abstractmethod
    def update_model_and_device(self, model_name: str, device: str):
        """
        如果服务支持，更新 ASR 模型和设备。

        这允许在不重新初始化整个服务的情况下更改设置。

        Args:
            model_name (str): 要使用的 ASR 模型名称（例如，“small”、“medium”）。
            device (str): 处理设备（“cpu”、“cuda”、“mps”）。
        """
        pass