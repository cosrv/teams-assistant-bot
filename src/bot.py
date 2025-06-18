# src/bot.py
import asyncio
import logging
from botbuilder.core import TurnContext
from botbuilder.integration.aiohttp import CloudAdapter, ConfigurationBotFrameworkAuthentication
from botbuilder.schema import Activity
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

# Create adapter with correct authentication
auth_settings = {
    "MicrosoftAppId": Config.APP_ID,
    "MicrosoftAppPassword": Config.APP_PASSWORD
}
auth_config = ConfigurationBotFrameworkAuthentication(auth_settings)
adapter = CloudAdapter(auth_config)

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

# Bot messages endpoint
@app.post("/api/messages")
async def messages(request: Request):
    """Handle bot messages"""
    # Get the raw body as JSON
    body = await request.json()
    
    if "type" not in body:
        return JSONResponse({"error": "Invalid activity"}, status_code=400)
    
    activity = Activity().deserialize(body)
    
    async def aux_func(turn_context):
        await bot.on_turn(turn_context)
    
    try:
        # Process the activity
        await adapter.process_activity(activity, "", aux_func)
        return JSONResponse({"status": "ok"})
    except Exception as e:
        logger.error(f"Error processing activity: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

# Main entry point
if __name__ == "__main__":
    logger.info(f"Starting bot on port {Config.PORT}")
    uvicorn.run(app, host="0.0.0.0", port=Config.PORT)