import logging
import sys
import json
from datetime import datetime

# Maximales Debug-Logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    stream=sys.stdout
)

# Alle Logger auf DEBUG
for logger_name in ['', 'botbuilder', 'botframework', 'msrest', 'urllib3', 'azure', 'openai']:
    logging.getLogger(logger_name).setLevel(logging.DEBUG)

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

logger.info("="*50)
logger.info(f"STARTING BOT DEBUG MODE")
logger.info(f"Time: {datetime.now()}")
logger.info(f"APP_ID: {Config.APP_ID}")
logger.info(f"APP_ID Length: {len(Config.APP_ID) if Config.APP_ID else 0}")
logger.info(f"Password exists: {bool(Config.APP_PASSWORD)}")
logger.info(f"Password length: {len(Config.APP_PASSWORD) if Config.APP_PASSWORD else 0}")
logger.info("="*50)

# Debug-Patch für validate_identity
import botframework.connector.auth.channel_validation as cv

original_validate = cv.ChannelValidation.validate_identity

async def debug_validate_identity(identity, credentials):
    logger.info(f"=== VALIDATE_IDENTITY DEBUG ===")
    logger.info(f"Identity claims: {identity.claims if hasattr(identity, 'claims') else 'No claims'}")
    logger.info(f"Credentials APP_ID: {credentials.microsoft_app_id if hasattr(credentials, 'microsoft_app_id') else 'No app_id'}")
    logger.info(f"Credentials type: {type(credentials)}")
    
    if hasattr(credentials, 'app_id'):
        logger.info(f"SimpleCredentialProvider APP_ID: {credentials.app_id}")
    
    try:
        result = await original_validate(identity, credentials)
        logger.info(f"Validation SUCCESS ✓")
        return result
    except Exception as e:
        logger.error(f"Validation FAILED: {e}")
        logger.error(f"Identity type: {type(identity)}")
        raise

cv.ChannelValidation.validate_identity = debug_validate_identity

app = FastAPI()

# Bot Framework Adapter mit Settings
try:
    # Bot Framework Adapter Settings
    settings = BotFrameworkAdapterSettings(
        app_id=Config.APP_ID,
        app_password=Config.APP_PASSWORD
    )
    logger.info(f"Created BotFrameworkAdapterSettings with app_id: {settings.app_id}")
    
    # BotFrameworkAdapter erstellen
    adapter = BotFrameworkAdapter(settings)
    logger.info("Adapter created successfully with BotFrameworkAdapter")
    
    # Error handler
    async def on_error(context: TurnContext, error: Exception):
        logger.error(f"Error in bot: {error}", exc_info=True)
        await context.send_activity("Entschuldigung, es ist ein Fehler aufgetreten.")
    
    adapter.on_turn_error = on_error
    
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

@app.get("/health")
async def health_check():
    return JSONResponse({
        "status": "healthy", 
        "debug": "active",
        "app_id": Config.APP_ID[:8] + "..." if Config.APP_ID else "NOT SET"
    })

@app.post("/api/messages")
async def messages(request: Request):
    logger.info("="*30 + " NEW REQUEST " + "="*30)
    
    # Headers
    headers = dict(request.headers)
    logger.info(f"Headers: {json.dumps({k: v[:50] + '...' if k.lower() == 'authorization' and len(v) > 50 else v for k, v in headers.items()}, indent=2)}")
    
    # Body als String und JSON
    body_bytes = await request.body()
    body_str = body_bytes.decode('utf-8')
    body_json = json.loads(body_str)
    
    logger.info(f"Body: {json.dumps(body_json, indent=2)}")
    
    # Auth Header Details
    auth_header = headers.get("authorization", "")
    if auth_header and " " in auth_header:
        parts = auth_header.split(" ")
        if len(parts) == 2 and parts[0] == "Bearer":
            token_parts = parts[1].split(".")
            logger.info(f"Token has {len(token_parts)} parts")
            if len(token_parts) == 3:
                try:
                    import base64
                    # Decode header
                    header = json.loads(base64.urlsafe_b64decode(token_parts[0] + "=="))
                    logger.info(f"Token Header: {json.dumps(header, indent=2)}")
                    
                    # Decode payload
                    payload = json.loads(base64.urlsafe_b64decode(token_parts[1] + "=="))
                    logger.info(f"Token Payload: {json.dumps(payload, indent=2)}")
                    
                    # Validierung der App ID
                    token_aud = payload.get('aud')
                    if token_aud != Config.APP_ID:
                        logger.error(f"Token audience mismatch! Token: {token_aud}, Config: {Config.APP_ID}")
                    else:
                        logger.info("Token audience matches configured App ID ✓")
                        
                except Exception as e:
                    logger.error(f"Failed to decode token: {e}")
    
    try:
        # Activity
        activity = Activity().deserialize(body_json)
        logger.info(f"Activity type: {activity.type}")
        
        # Direkte JWT Validierung mit SimpleCredentialProvider
        credential_provider = SimpleCredentialProvider(Config.APP_ID, Config.APP_PASSWORD)
        
        # Authenticate
        try:
            claims = await JwtTokenValidation.authenticate_request(
                activity, auth_header, credential_provider
            )
            logger.info(f"JWT Validation SUCCESS! Claims: {claims.claims if hasattr(claims, 'claims') else claims}")
        except Exception as e:
            logger.error(f"JWT Validation failed: {e}")
            return JSONResponse({"error": "Authentication failed"}, status_code=401)
            
        # Bot Context erstellen
        turn_context = TurnContext(adapter, activity)
        
        # ConnectorClient erstellen und hinzufügen
        credentials = MicrosoftAppCredentials(Config.APP_ID, Config.APP_PASSWORD)
        connector = ConnectorClient(credentials, base_url=activity.service_url)
        turn_context.turn_state["BotIdentity"] = claims
        turn_context.turn_state["ConnectorClient"] = connector
        
        # Bot aufrufen
        logger.info("Calling bot.on_turn...")
        await bot.on_turn(turn_context)
        logger.info("bot.on_turn completed successfully ✓")
        
        # Responses senden
        if hasattr(turn_context, '_activity') and turn_context._activity.type == "invoke":
            invoke_response = turn_context.turn_state.get("InvokeResponseKey")
            if invoke_response:
                return JSONResponse(
                    content=invoke_response.body,
                    status_code=invoke_response.status
                )
        
        return JSONResponse({"status": "ok"})
        
    except Exception as e:
        logger.error(f"Error: {type(e).__name__}: {str(e)}", exc_info=True)
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

if __name__ == "__main__":
    logger.info(f"Starting bot on port {Config.PORT}")
    logger.info(f"Bot ready to receive messages!")
    uvicorn.run(app, host="0.0.0.0", port=Config.PORT, log_level="info")
