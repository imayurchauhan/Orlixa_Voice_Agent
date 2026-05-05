import pyttsx3
from utils.logger import get_logger
import config

logger = get_logger()

class TextToSpeech:
    def __init__(self):
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', config.VOICE_RATE)
            logger.info("TTS engine initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            self.engine = None

    def speak(self, text):
        if not self.engine:
            logger.warning("TTS engine is not initialized. Attempting re-init...")
            try:
                self.engine = pyttsx3.init()
            except:
                return
        
        try:
            logger.info(f"{config.ASSISTANT_NAME}: {text}")
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            logger.error(f"Error during TTS speak: {e}")
            # If a pipe error occurs, the engine state might be corrupted.
            # Resetting the engine can sometimes help for the next call.
            try:
                self.engine = pyttsx3.init()
            except:
                self.engine = None
