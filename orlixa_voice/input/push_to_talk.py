import keyboard
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
from utils.logger import get_logger
import config
import tempfile
import os
import time

logger = get_logger()

class PushToTalk:
    def __init__(self):
        self.sample_rate = config.WHISPER_SAMPLE_RATE
        self.channels = 1
        self.recording = False
        self.audio_data = []

    def record_audio(self):
        logger.info(f"Press and hold '{config.PUSH_KEY}' to speak...")
        
        while not keyboard.is_pressed(config.PUSH_KEY):
            time.sleep(0.1)

        logger.info("Recording started. Release to stop.")
        
        self.recording = True
        self.audio_data = []

        def callback(indata, frames, time_info, status):
            if status:
                logger.warning(f"Audio status: {status}")
            if self.recording:
                self.audio_data.append(indata.copy())

        stream = sd.InputStream(samplerate=self.sample_rate, channels=self.channels, callback=callback)
        
        with stream:
            while keyboard.is_pressed(config.PUSH_KEY):
                sd.sleep(100)
            
        self.recording = False
        logger.info("Recording stopped.")

        if not self.audio_data:
            return None

        audio_array = np.concatenate(self.audio_data, axis=0)
        
        # Save to temporary file
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, "orlixa_record.wav")
        
        wav.write(temp_file, self.sample_rate, audio_array)
        return temp_file
