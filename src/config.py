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

# Debug output
print(f"Config loaded - APP_ID: {Config.APP_ID}")
print(f"Config loaded - APP_ID present: {bool(Config.APP_ID)}")
print(f"Config loaded - APP_PASSWORD present: {bool(Config.APP_PASSWORD)}")