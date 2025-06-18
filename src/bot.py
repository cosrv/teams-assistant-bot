# src/bot.py
import asyncio
import logging
from botbuilder.core import TurnContext
from botbuilder.integration.aiohttp import CloudAdapter
from botbuilder.schema import Activity
from botframework.connector.auth import SimpleCredentialProvider, MicrosoftAppCredentials
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

# Create credentials and adapter - VEREINFACHTE VERSION
credentials = SimpleCredentialProvider(
    app_id=Config.APP_ID,
    password=Config.APP_PASSWORD
)

# Create adapter with credentials
adapter = CloudAdapter(credentials)

# Error handler
async def on_error(context: TurnContext, error: Exception):
    logger.error(f"Error in bot: {error}")
    await context.send_activity("Entschuldigung, es ist ein Fehler aufgetreten.")

adapter.on_turn_error = on_error

# Create bot
try:
    assistant_manager = AssistantManager(Config.OPENAI_API_KEY, Config.ASSISTANT_ID)
    bot = TeamsAssistantBot(assistant_manager)
    logger.info(f"Bot initialized with App ID: {Config.APP_ID[:8]}...")
except Exception as e:
    logger.error(f"Failed to initialize bot: {e}")
    raise

# Health check endpoint
@app.get("/health")
async def health_check():
    return JSONResponse({
        "status": "healthy", 
        "service": "teams-assistant-bot",
        "app_id_configured": bool(Config.APP_ID)
    })

# Bot messages endpoint
@app.post("/api/messages")
async def messages(request: Request):
    """Handle bot messages"""
    if "application/json" not in request.headers.get("content-type", ""):
        return JSONResponse({"error": "Invalid content type"}, status_code=415)
    
    body = await request.json()
    activity = Activity().deserialize(body)
    
    # Get auth header
    auth_header = request.headers.get("Authorization", "")
    
    try:
        # Create response function
        async def call_bot(turn_context):
            await bot.on_turn(turn_context)
        
        # Process activity
        await adapter.process_activity(auth_header, activity, call_bot)
        return JSONResponse({"status": "ok"})
    except Exception as e:
        logger.error(f"Error processing activity: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

# Handle OPTIONS requests for CORS
@app.options("/api/messages")
async def messages_options():
    return JSONResponse(
        {"status": "ok"},
        headers={
            "Allow": "POST, OPTIONS",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type"
        }
    )

# Main entry point
if __name__ == "__main__":
    logger.info(f"Starting bot on port {Config.PORT}")
    logger.info(f"App ID configured: {Config.APP_ID[:8]}...")
    uvicorn.run(app, host="0.0.0.0", port=Config.PORT)