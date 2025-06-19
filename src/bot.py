import logging
import sys
import json
import os
from datetime import datetime

# Logging Level aus Umgebungsvariable oder Standard INFO
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

# Basis-Logging Konfiguration
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

# Spezifische Logger auf WARNING setzen (diese sind sehr verbose)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('msrest').setLevel(logging.WARNING)
logging.getLogger('azure').setLevel(logging.WARNING)
logging.getLogger('msal').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.WARNING)

# Bot Framework Logger auf INFO
logging.getLogger('botbuilder').setLevel(logging.INFO)
logging.getLogger('botframework').setLevel(logging.INFO)

logger = logging.getLogger(__name__)

from botbuilder.core import TurnContext, BotFrameworkAdapter, BotFrameworkAdapterSettings
from botbuilder.schema import Activity, InvokeResponse
from botframework.connector import ConnectorClient
from botframework.connector.auth import JwtTokenValidation, SimpleCredentialProvider, MicrosoftAppCredentials
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

from .config import Config
from .assistant_manager import AssistantManager
from .teams_handler import TeamsAssistantBot

# Startup Info (nur einmal)
logger.info("="*50)
logger.info(f"Starting Bot - Version 1.0")
logger.info(f"Time: {datetime.now()}")
logger.info(f"Log Level: {LOG_LEVEL}")
logger.info(f"APP_ID configured: {'Yes' if Config.APP_ID else 'No'}")
logger.info("="*50)

app = FastAPI()

# Bot Framework Adapter
try:
    settings = BotFrameworkAdapterSettings(
        app_id=Config.APP_ID,
        app_password=Config.APP_PASSWORD
    )
    
    adapter = BotFrameworkAdapter(settings)
    
    # Error handler
    async def on_error(context: TurnContext, error: Exception):
        logger.error(f"Error in bot: {error}", exc_info=True)
        await context.send_activity("Entschuldigung, es ist ein Fehler aufgetreten.")
    
    adapter.on_turn_error = on_error
    logger.info("Bot Framework Adapter initialized successfully")
    
except Exception as e:
    logger.error(f"Failed to create adapter: {e}", exc_info=True)
    raise

# Bot initialisieren
try:
    assistant_manager = AssistantManager(Config.OPENAI_API_KEY, Config.ASSISTANT_ID)
    bot = TeamsAssistantBot(assistant_manager)
    logger.info("Bot initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize bot: {e}", exc_info=True)
    raise

# Request Counter für Basic Monitoring
request_count = 0
message_count = 0

@app.get("/health")
async def health_check():
    return JSONResponse({
        "status": "healthy",
        "requests_processed": request_count,
        "messages_processed": message_count,
        "log_level": LOG_LEVEL
    })

@app.post("/api/messages")
async def messages(request: Request):
    global request_count, message_count
    request_count += 1
    
    try:
        # Headers
        headers = dict(request.headers)
        auth_header = headers.get("authorization", "")
        
        # Body
        body_bytes = await request.body()
        body_str = body_bytes.decode('utf-8')
        body_json = json.loads(body_str)
        
        # Activity
        activity = Activity().deserialize(body_json)
        
        # Logging OHNE Nachrichteninhalt
        logger.info(f"Activity: type={activity.type}, "
                   f"from_id={activity.from_property.id if activity.from_property else 'unknown'}, "
                   f"channel={activity.channel_id}")
        
        # Bei message activities nur zählen, nicht loggen
        if activity.type == "message":
            message_count += 1
            logger.info(f"Processing message #{message_count}")
            # KEIN Logging des Nachrichtentexts!
        
        # JWT Validierung
        credential_provider = SimpleCredentialProvider(Config.APP_ID, Config.APP_PASSWORD)
        
        try:
            claims = await JwtTokenValidation.authenticate_request(
                activity, auth_header, credential_provider
            )
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("JWT validation successful")
        except Exception as e:
            logger.error(f"JWT Validation failed: {e}")
            return JSONResponse({"error": "Authentication failed"}, status_code=401)
        
        # Bot Context
        turn_context = TurnContext(adapter, activity)
        
        # ConnectorClient
        credentials = MicrosoftAppCredentials(Config.APP_ID, Config.APP_PASSWORD)
        connector = ConnectorClient(credentials, base_url=activity.service_url)
        turn_context.turn_state["BotIdentity"] = claims
        turn_context.turn_state["ConnectorClient"] = connector
        
        # Bot aufrufen
        await bot.on_turn(turn_context)
        
        # Response handling für invoke activities
        if hasattr(turn_context, '_activity') and turn_context._activity.type == "invoke":
            invoke_response = turn_context.turn_state.get("InvokeResponseKey")
            if invoke_response:
                return JSONResponse(
                    content=invoke_response.body,
                    status_code=invoke_response.status
                )
        
        return JSONResponse({"status": "ok"})
        
    except Exception as e:
        logger.error(f"Error processing request: {type(e).__name__}: {str(e)}")
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Full error details:", exc_info=True)
        return JSONResponse({"error": str(e)}, status_code=500)

@app.options("/api/messages")
async def messages_options():
    """Handle OPTIONS requests for CORS"""
    return JSONResponse(
        {"status": "ok"},
        headers={
            "Allow": "POST, OPTIONS",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type"
        }
    )

# Startup event für einmalige Logs
@app.on_event("startup")
async def startup_event():
    logger.info(f"Bot API started on port {Config.PORT}")
    logger.info("Ready to receive messages!")

if __name__ == "__main__":
    # Uvicorn mit reduziertem Logging
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=Config.PORT, 
        log_level="info",
        access_log=False  # Deaktiviert Request-Logs von Uvicorn
    )