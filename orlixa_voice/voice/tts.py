import pyttsx3
from utils.logger import get_logger
import config
import threading
import time

logger = get_logger()

class TextToSpeech:
    def __init__(self):
        self.lock = threading.Lock()
        self._init_engine()

    def _init_engine(self):
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', config.VOICE_RATE)
            logger.info("TTS engine initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            self.engine = None

    def speak(self, text):
        if not text:
            return
            
        with self.lock:
            if not self.engine:
                self._init_engine()
                if not self.engine:
                    return

            try:
                logger.info(f"{config.ASSISTANT_NAME}: {text}")
                self.engine.say(text)
                self.engine.runAndWait()
                # Small pause to ensure the engine pipe is cleared
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error during TTS speak: {e}")
                # Reset engine on failure
                self._init_engine()
                try:
                    # Final attempt
                    self.engine.say(text)
                    self.engine.runAndWait()
                except:
                    pass
