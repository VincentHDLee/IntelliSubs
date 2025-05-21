# Audio Processing Utilities

import ffmpeg
from pydub import AudioSegment
import os
import logging

class AudioProcessor:
    def __init__(self, target_sample_rate: int = 16000, target_channels: int = 1, target_format: str = "wav", logger: logging.Logger = None):
        """
        Initializes the AudioProcessor.

        Args:
            target_sample_rate (int): Desired sample rate for processed audio.
            target_channels (int): Desired number of channels for processed audio (1 for mono).
            target_format (str): Desired output format (e.g., "wav").
            logger (logging.Logger, optional): Logger instance.
        """
        self.logger = logger if logger else logging.getLogger(self.__class__.__name__)
        self.target_sample_rate = target_sample_rate
        self.target_channels = target_channels
        self.target_format = target_format
        self.logger.info(f"AudioProcessor initialized for {target_sample_rate}Hz, {target_channels}ch, {target_format}")

    def preprocess_audio(self, input_path: str, output_path: str) -> str:
        """
        Preprocesses an audio file:
        - Converts to a standard format (e.g., 16kHz, mono, WAV).
        - (Optional) Applies noise reduction.
        - (Optional) Extracts audio track from video.

        Args:
            input_path (str): Path to the input audio or video file.
            output_path (str): Path to save the preprocessed audio file.

        Returns:
            str: Path to the preprocessed audio file.
        """
        # Check if input is a video file based on common extensions
        video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.flv', '.webm']
        input_ext = os.path.splitext(input_path)[1].lower()

        temp_audio_path = input_path
        if input_ext in video_extensions:
            self.logger.info(f"检测到视频文件 '{input_path}'，正在提取音频...")
            temp_audio_path = f"{output_path}.temp_extracted_audio.wav" # Extract to a temp WAV
            try:
                self.extract_audio_from_video(input_path, temp_audio_path)
                self.logger.info(f"音频已从视频中提取到: {temp_audio_path}")
            except Exception as e:
                self.logger.error(f"从视频提取音频失败: {e}", exc_info=True)
                raise RuntimeError(f"从视频提取音频失败: {e}")

        self.logger.info(f"正在将 '{temp_audio_path}' 转换为标准格式 '{output_path}'...")
        try:
            self.convert_to_standard_format(temp_audio_path, output_path)
            self.logger.info(f"音频预处理完成，文件保存到: {output_path}")
        except Exception as e:
            self.logger.error(f"音频格式转换失败: {e}", exc_info=True)
            raise RuntimeError(f"音频格式转换失败: {e}")
        finally:
            if input_ext in video_extensions and os.path.exists(temp_audio_path):
                os.remove(temp_audio_path) # Clean up temporary extracted audio file
                self.logger.debug(f"已删除临时音频文件: {temp_audio_path}")

        return output_path

    def extract_audio_from_video(self, video_path: str, audio_output_path: str) -> str:
        """
        Extracts audio track from a video file.

        Args:
            video_path (str): Path to the video file.
            audio_output_path (str): Path to save the extracted audio.

        Returns:
            str: Path to the extracted audio file.
        """
        self.logger.info(f"尝试使用ffmpeg从视频中提取音频: {video_path}")
        try:
            ffmpeg.input(video_path).output(audio_output_path, acodec='pcm_s16le', ac=self.target_channels, ar=self.target_sample_rate).run(overwrite_output=True, quiet=True)
            self.logger.info(f"音频已成功提取到: {audio_output_path}")
            return audio_output_path
        except ffmpeg.Error as e:
            self.logger.error(f"FFmpeg提取音频时出错: {e.stderr.decode()}", exc_info=True)
            raise RuntimeError(f"FFmpeg提取音频时出错: {e.stderr.decode()}")
        except Exception as e:
            self.logger.error(f"提取音频时发生意外错误: {e}", exc_info=True)
            raise RuntimeError(f"提取音频时发生意外错误: {e}")

    def convert_to_standard_format(self, input_path: str, output_path: str):
        """
        Converts audio to the standard format (sample rate, channels, format).
        This uses ffmpeg to ensure compatibility with ASR models.
        """
        self.logger.info(f"尝试使用ffmpeg将 '{input_path}' 转换为标准格式 '{output_path}'...")
        try:
            ffmpeg.input(input_path).output(
                output_path,
                acodec='pcm_s16le', # PCM 16-bit little-endian for raw audio, widely compatible
                ac=self.target_channels,    # Audio channels
                ar=self.target_sample_rate, # Audio sample rate
                f=self.target_format        # Output format
            ).run(overwrite_output=True, quiet=True)
            self.logger.info(f"音频已成功转换为标准格式: {output_path}")
            return output_path
        except ffmpeg.Error as e:
            self.logger.error(f"FFmpeg转换音频格式时出错: {e.stderr.decode()}", exc_info=True)
            raise RuntimeError(f"FFmpeg转换音频格式时出错: {e.stderr.decode()}")
        except Exception as e:
            self.logger.error(f"转换音频格式时发生意外错误: {e}", exc_info=True)
            raise RuntimeError(f"转换音频格式时发生意外错误: {e}")

    # Noise reduction is currently low priority based on DEVELOPMENT.md
    # def apply_noise_reduction(self, input_path: str, output_path: str):
    #     """
    #     Applies noise reduction to an audio file.
    #     This would typically use noisereduce.
    #     """
    #     self.logger.info(f"Applying noise reduction to {input_path}, saving to {output_path}...")
    #     # Placeholder for noisereduce logic if implemented
    #     self.logger.info(f"Noise reduction complete: {output_path}")
    #     return output_path