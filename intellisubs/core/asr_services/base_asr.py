# Base class for ASR services
from abc import ABC, abstractmethod

class BaseASRService(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str) -> list:
        """
        Transcribes the given audio file.

        Args:
            audio_path (str): Path to the audio file.

        Returns:
            list: A list of transcribed segments, where each segment
                  might be a dictionary скорость or object containing
                  text, start_time, end_time.
        """
        pass