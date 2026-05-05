import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Identity
ASSISTANT_NAME = "Orlixa"

# Push to talk key
PUSH_KEY = "ctrl+space"

# Whisper settings
MODEL_SIZE = "small"
WHISPER_SAMPLE_RATE = 16000

# Text to Speech settings
VOICE_RATE = 170

# Paths
LOG_FILE = "logs/orlixa.log"
DB_PATH = "database/orlixa.db"

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
