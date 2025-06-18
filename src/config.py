# src/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Azure Bot
    APP_ID = os.getenv("APP_ID")
    APP_PASSWORD = os.getenv("APP_PASSWORD")
    
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ASSISTANT_ID = os.getenv("ASSISTANT_ID")
    
    # Server
    PORT = int(os.getenv("PORT", 3978))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")