from faster_whisper import WhisperModel
from utils.logger import get_logger
import config

logger = get_logger()

class SpeechToText:
    def __init__(self):
        logger.info(f"Loading Whisper model: {config.MODEL_SIZE}")
        try:
            self.model = WhisperModel(config.MODEL_SIZE, device="cpu", compute_type="float32")
            logger.info("Whisper model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            self.model = None

    def transcribe(self, audio_file):
        if not self.model:
            logger.error("Whisper model is not initialized.")
            return ""
        
        try:
            logger.info("Starting transcription...")
            segments, info = self.model.transcribe(audio_file, beam_size=5)
            text = " ".join([segment.text for segment in segments])
            logger.info(f"Transcription complete: {text}")
            return text.strip()
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return ""
