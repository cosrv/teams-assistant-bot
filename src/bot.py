# src/bot.py
import asyncio
import logging
from aiohttp import web
from botbuilder.core import TurnContext
from botframework.connector.auth import SimpleCredentialProvider
from botbuilder.integration.aiohttp import CloudAdapter, ConfigurationBotFrameworkAuthentication
from botbuilder.schema import Activity
from fastapi import FastAPI
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

# Create adapter
auth_config = ConfigurationBotFrameworkAuthentication(
    app_id=Config.APP_ID,
    app_password=Config.APP_PASSWORD
)
adapter = CloudAdapter(auth_config)

# Error handler
async def on_error(context: TurnContext, error: Exception):
    logger.error(f"Error: {error}")
    await context.send_activity("Entschuldigung, es ist ein Fehler aufgetreten.")

adapter.on_turn_error = on_error

# Create bot
assistant_manager = AssistantManager(Config.OPENAI_API_KEY, Config.ASSISTANT_ID)
bot = TeamsAssistantBot(assistant_manager)

# Health check endpoint
@app.get("/health")
async def health_check():
    return JSONResponse({"status": "healthy", "service": "teams-assistant-bot"})

# Bot messages endpoint
@app.post("/api/messages")
async def messages(req: dict):
    """Handle bot messages"""
    if "type" not in req:
        return JSONResponse({"error": "Invalid activity"}, status_code=400)
    
    activity = Activity().deserialize(req)
    
    async def aux_func(turn_context):
        await bot.on_turn(turn_context)
    
    try:
        await adapter.process_activity(activity, "", aux_func)
        return JSONResponse({"status": "ok"})
    except Exception as e:
        logger.error(f"Error processing activity: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

# Main entry point
if __name__ == "__main__":
    logger.info(f"Starting bot on port {Config.PORT}")
    uvicorn.run(app, host="0.0.0.0", port=Config.PORT)