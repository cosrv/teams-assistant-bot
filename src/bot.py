# src/bot.py
import asyncio
import logging
from botbuilder.core import TurnContext
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.integration.aiohttp import CloudAdapter, ConfigurationBotFrameworkAuthentication
from botbuilder.schema import Activity
from botframework.connector.auth import AuthenticationConfiguration
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

from .config import Config
from .assistant_manager import AssistantManager
from .teams_handler import TeamsAssistantBot

# Setup logging
logging.basicConfig(
    level=Config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI()

# Create adapter - KORRIGIERTE VERSION
adapter_settings = ConfigurationBotFrameworkAuthentication(
    {"MicrosoftAppId": Config.APP_ID, "MicrosoftAppPassword": Config.APP_PASSWORD}
)
adapter = CloudAdapter(adapter_settings)

# Error handler
async def on_error(context: TurnContext, error: Exception):
    logger.error(f"Error: {error}")
    await context.send_activity("Entschuldigung, es ist ein Fehler aufgetreten.")

adapter.on_turn_error = on_error

# Create bot
try:
    assistant_manager = AssistantManager(Config.OPENAI_API_KEY, Config.ASSISTANT_ID)
    bot = TeamsAssistantBot(assistant_manager)
    logger.info("Bot successfully initialized")
except Exception as e:
    logger.error(f"Failed to initialize bot: {e}")
    raise

# Health check endpoint
@app.get("/health")
async def health_check():
    return JSONResponse({"status": "healthy", "service": "teams-assistant-bot"})

# Bot messages endpoint - KORRIGIERTE VERSION
@app.post("/api/messages")
async def messages(request: Request):
    """Handle bot messages"""
    if "application/json" not in request.headers.get("content-type", ""):
        return JSONResponse({"error": "Invalid content type"}, status_code=415)
    
    body = await request.json()
    activity = Activity().deserialize(body)
    
    # WICHTIG: auth_header aus Request extrahieren
    auth_header = request.headers.get("Authorization", "")
    
    try:
        # Korrigierter Aufruf mit auth_header statt string
        async def call_bot(turn_context):
            await bot.on_turn(turn_context)
        
        await adapter.process_activity(auth_header, activity, call_bot)
        return JSONResponse({"status": "ok"})
    except Exception as e:
        logger.error(f"Error processing activity: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

# Main entry point
if __name__ == "__main__":
    logger.info(f"Starting bot on port {Config.PORT}")
    uvicorn.run(app, host="0.0.0.0", port=Config.PORT)