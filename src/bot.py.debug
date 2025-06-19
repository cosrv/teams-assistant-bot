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

from botbuilder.core import TurnContext
from botbuilder.integration.aiohttp import CloudAdapter, ConfigurationBotFrameworkAuthentication
from botbuilder.schema import Activity
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

# Nach den imports, vor der App-Erstellung
import botframework.connector.auth.channel_validation as cv

# Monkey-patch für mehr Debug
original_validate = cv.ChannelValidation.validate_identity

async def debug_validate_identity(identity, credentials):
    logger.info(f"=== VALIDATE_IDENTITY DEBUG ===")
    logger.info(f"Identity claims: {identity.claims if hasattr(identity, 'claims') else 'No claims'}")
    logger.info(f"Credentials APP_ID: {credentials.microsoft_app_id if hasattr(credentials, 'microsoft_app_id') else 'No app_id'}")

    # Original aufrufen
    try:
        result = await original_validate(identity, credentials)
        logger.info(f"Validation SUCCESS")
        return result
    except Exception as e:
        logger.error(f"Validation FAILED: {e}")
        logger.error(f"Identity type: {type(identity)}")
        logger.error(f"Credentials type: {type(credentials)}")
        raise

cv.ChannelValidation.validate_identity = debug_validate_identity

app = FastAPI()

# Adapter mit Debug
try:
    config_dict = {
        "MicrosoftAppId": Config.APP_ID,
        "MicrosoftAppPassword": Config.APP_PASSWORD,
        "MicrosoftAppType": "MultiTenant",
        "MicrosoftAppTenantId": ""
    }
    logger.info(f"Creating adapter with config: {json.dumps({k: v if k != 'MicrosoftAppPassword' else '***' for k, v in config_dict.items()})}")
    
    auth_config = ConfigurationBotFrameworkAuthentication(config_dict)
    adapter = CloudAdapter(auth_config)
    logger.info("Adapter created successfully")
except Exception as e:
    logger.error(f"Failed to create adapter: {e}", exc_info=True)
    raise

# Bot
assistant_manager = AssistantManager(Config.OPENAI_API_KEY, Config.ASSISTANT_ID)
bot = TeamsAssistantBot(assistant_manager)

@app.get("/health")
async def health_check():
    return JSONResponse({"status": "healthy", "debug": "active"})

@app.post("/api/messages")
async def messages(request: Request):
    logger.info("="*30 + " NEW REQUEST " + "="*30)
    
    # Headers
    headers = dict(request.headers)
    logger.info(f"Headers: {json.dumps({k: v[:50] + '...' if k.lower() == 'authorization' and len(v) > 50 else v for k, v in headers.items()}, indent=2)}")
    
    # Body
    body = await request.json()
    logger.info(f"Body: {json.dumps(body, indent=2)}")
    
    # Auth Header Details
    auth_header = headers.get("authorization", "")
    if auth_header:
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
                except Exception as e:
                    logger.error(f"Failed to decode token: {e}")
    
    try:
        activity = Activity().deserialize(body)
        
        async def turn_handler(context):
            await bot.on_turn(context)
        
        logger.info("Calling adapter.process_activity...")
        await adapter.process_activity(auth_header, activity, turn_handler)
        logger.info("adapter.process_activity completed successfully")
        
        return JSONResponse({"status": "ok"})
        
    except Exception as e:
        logger.error(f"Error: {type(e).__name__}: {str(e)}", exc_info=True)
        return JSONResponse({"error": str(e)}, status_code=500)

if __name__ == "__main__":
    logger.info(f"Starting bot on port {Config.PORT}")
    uvicorn.run(app, host="0.0.0.0", port=Config.PORT, log_level="debug")
