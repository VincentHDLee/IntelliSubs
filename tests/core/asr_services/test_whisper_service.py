import unittest
import logging
from unittest.mock import MagicMock, patch

# Attempt to import WhisperModel for type hinting and spec for MagicMock
# This might fail if faster_whisper is not installed, but it's good for dev.
try:
    from faster_whisper import WhisperModel
    # For creating mock return values that mimic the actual structure:
    from faster_whisper.transcribe import Segment as ActualSegment, Word as ActualWord, TranscriptionInfo as ActualTranscriptionInfo
except ImportError:
    # Define dummy types if faster_whisper is not available (e.g. in a very minimal CI setup phase)
    # This allows the test file to be syntactically correct even if deps are missing.
    WhisperModel = type('WhisperModel', (object,), {})
    ActualSegment = type('Segment', (object,), {})
    ActualWord = type('Word', (object,), {})
    ActualTranscriptionInfo = type('TranscriptionInfo', (object,), {})


from intellisubs.core.asr_services.whisper_service import WhisperService

# Setup basic logging for tests
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class TestWhisperService(unittest.TestCase):

    def setUp(self):
        """Set up for each test method."""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Create a mock for the WhisperModel instance that WhisperService will use
        self.mock_whisper_model_instance = MagicMock(spec=WhisperModel) 
        
        # Configure the mock's transcribe method to return a plausible structure
        # Use actual types if available, otherwise use dicts as fallback for mock structure
        if ActualWord is not type:
            mock_word = ActualWord(start=0.0, end=1.0, word="dummy", probability=0.9)
        else:
            mock_word = {"start":0.0, "end":1.0, "word":"dummy", "probability":0.9}

        if ActualSegment is not type:
            mock_segment = ActualSegment(
                start=0.0, end=1.0, text="dummy transcription", words=[mock_word],
                id=0, seek=0, tokens=[123], temperature=0.0, avg_logprob=-0.5,
                compression_ratio=1.5, no_speech_prob=0.1,
            )
        else: # Fallback mock structure for Segment
            mock_segment = {"text": "dummy transcription", "start": 0.0, "end": 1.0, "words": [mock_word]}

        if ActualTranscriptionInfo is not type:
            mock_transcription_info = ActualTranscriptionInfo(
                language="en", language_probability=0.99, duration=1.0,
                duration_after_vad=1.0, all_language_probs=[("en", 0.99)],
                vad_level_durations=[] 
            )
        else: # Fallback for TranscriptionInfo
            mock_transcription_info = {"language": "en", "language_probability": 0.99, "duration": 1.0}

        self.mock_whisper_model_instance.transcribe.return_value = ([mock_segment], mock_transcription_info)

        # Patch 'faster_whisper.WhisperModel' in the module where WhisperService imports it.
        # This ensures that when WhisperService tries to create a WhisperModel, it gets our mock_whisper_model_instance.
        self.patcher = patch('intellisubs.core.asr_services.whisper_service.WhisperModel', return_value=self.mock_whisper_model_instance)
        
        self.MockWhisperModelClass_PATCHED = self.patcher.start() # This is the patched CLASS

        # Now, when WhisperService is instantiated, it will call the patched WhisperModel class,
        # which will return self.mock_whisper_model_instance.
        self.service_cpu = WhisperService(model_name="tiny", device="cpu", logger=self.logger)
        # So, self.service_cpu._model should be self.mock_whisper_model_instance

    def tearDown(self):
        """Clean up after each test method by stopping the patcher."""
        self.patcher.stop()

    def test_transcribe_cpu_placeholder(self):
        """Test basic transcription using the mocked model."""
        # The "dummy_audio.wav" path is passed but won't be used by the mocked transcribe.
        # We pass language="en" to match the mocked TranscriptionInfo.
        segments_result, info_result = self.service_cpu.transcribe("dummy_audio.wav", language="en")
        
        self.assertIsNotNone(segments_result, "Segments should not be None")
        self.assertEqual(len(segments_result), 1, "Should produce one mocked segment")
        
        # Access attributes based on whether it's a real Segment object or a fallback dict
        # Based on the mock setup, segments_result[0] will be the mock_segment object or dict
        if ActualSegment is not type: # If we had the real type
            self.assertEqual(segments_result[0].text, "dummy transcription", "Segment text should match mock")
        else: # Fallback for when Segment type was dummied
             # This check assumes mock_segment was a dict if ActualSegment wasn't available
            if isinstance(segments_result[0], dict):
                 self.assertEqual(segments_result[0]["text"], "dummy transcription", "Segment text should match mock")
            else: # It might be a MagicMock itself if spec was used correctly even with dummy type
                 self.assertEqual(segments_result[0].text, "dummy transcription", "Segment text should match mock")


        self.assertIsNotNone(info_result, "Info should not be None")
        if ActualTranscriptionInfo is not type: # If we had the real type
            self.assertEqual(info_result.language, "en", "Language in info should match mock")
            self.assertEqual(info_result.language_probability, 0.99, "Lang probability should match mock")
        else: # Fallback
            if isinstance(info_result, dict):
                self.assertEqual(info_result["language"], "en", "Language in info should match mock")
                self.assertEqual(info_result["language_probability"], 0.99, "Lang probability should match mock")
            else:
                self.assertEqual(info_result.language, "en", "Language in info should match mock")
                self.assertEqual(info_result.language_probability, 0.99, "Lang probability should match mock")


        # Verify that the mock model's transcribe method (which is self.service_cpu._model.transcribe)
        # was called correctly.
        self.service_cpu._model.transcribe.assert_called_once_with(
            "dummy_audio.wav", 
            language="en", 
            beam_size=5 # Default beam_size in WhisperService.transcribe
        )

if __name__ == '__main__':
    unittest.main()