# src/teams_handler.py
from botbuilder.core import TurnContext, ActivityHandler, MessageFactory
from botbuilder.schema import ChannelAccount, Activity, ActivityTypes
import logging
import asyncio
import os

logger = logging.getLogger(__name__)

class TeamsAssistantBot(ActivityHandler):
    def __init__(self, assistant_manager):
        super().__init__()
        self.assistant_manager = assistant_manager
        
        # Liste der erlaubten Tenant IDs (deine Organisation + Partner)
        self.allowed_tenants = []
        
        # Aus Umgebungsvariable laden
        allowed_tenants_env = os.getenv("ALLOWED_TENANT_IDS", "")
        if allowed_tenants_env:
            self.allowed_tenants = [tid.strip() for tid in allowed_tenants_env.split(",")]
    
    async def on_message_activity(self, turn_context: TurnContext) -> None:
        """Handle incoming messages"""
        
        # Sicherheitsprüfung: Tenant validieren (wenn konfiguriert)
        if self.allowed_tenants and not await self._validate_tenant(turn_context):
            await turn_context.send_activity(
                MessageFactory.text("Zugriff verweigert. Dieser Bot ist nur für autorisierte Organisationen verfügbar.")
            )
            logger.warning(f"Unauthorized access attempt from tenant: {self._get_tenant_id(turn_context)}")
            return
        
        # Get user info - OHNE Nachrichtentext zu loggen
        user_id = turn_context.activity.from_property.id
        message = turn_context.activity.text
        
        # Nur User ID loggen, NICHT den Nachrichteninhalt
        logger.info(f"Processing message from user_id: {user_id}")
        logger.info(f"Channel: {turn_context.activity.channel_id}")
        
        # Check if it's a 1:1 conversation
        is_personal = (
            turn_context.activity.conversation.conversation_type == "personal" or
            turn_context.activity.channel_id == "webchat" or
            turn_context.activity.conversation.conversation_type is None or
            turn_context.activity.conversation.conversation_type == ""
        )
        
        if is_personal:
            try:
                # Show typing indicator
                typing_activity = MessageFactory.typing()
                await self._safe_send_activity(turn_context, typing_activity)
                
                # Get response from assistant
                response = await self.assistant_manager.get_response(user_id, message)
                
                # Send response
                await self._safe_send_activity(turn_context, MessageFactory.text(response))
                
                logger.info(f"Response sent to user_id: {user_id}")
                
            except Exception as e:
                logger.error(f"Error in message handling: {e}", exc_info=True)
                await self._safe_send_activity(
                    turn_context, 
                    MessageFactory.text("Entschuldigung, es ist ein Fehler aufgetreten. Bitte versuchen Sie es später erneut.")
                )
        else:
            logger.info("Ignoring message in group conversation")
    
    async def on_members_added_activity(self, members_added: list[ChannelAccount], turn_context: TurnContext) -> None:
        """Welcome new members"""
        
        # Sicherheitsprüfung auch hier
        if self.allowed_tenants and not await self._validate_tenant(turn_context):
            return
            
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                try:
                    welcome_message = MessageFactory.text(
                        "Hallo! Ich bin Ihr persönlicher Assistent. "
                        "Schreiben Sie mir einfach eine direkte Nachricht, und ich helfe Ihnen gerne weiter."
                    )
                    await self._safe_send_activity(turn_context, welcome_message)
                    logger.info("Welcome message sent")
                except Exception as e:
                    logger.error(f"Error sending welcome message: {e}", exc_info=True)
    
    def _get_tenant_id(self, turn_context: TurnContext) -> str:
        """Extract tenant ID from the turn context"""
        if hasattr(turn_context.activity, 'channel_data') and turn_context.activity.channel_data:
            channel_data = turn_context.activity.channel_data
            if isinstance(channel_data, dict):
                if 'tenant' in channel_data and isinstance(channel_data['tenant'], dict):
                    return channel_data['tenant'].get('id', '')
        
        if hasattr(turn_context.activity.conversation, 'tenant_id'):
            return turn_context.activity.conversation.tenant_id or ''
            
        return ''
    
    async def _validate_tenant(self, turn_context: TurnContext) -> bool:
        """Validate if the request comes from an allowed tenant"""
        # Webchat hat keine Tenant ID - das ist OK für Tests
        if turn_context.activity.channel_id == "webchat":
            return True
            
        # Wenn keine Tenants konfiguriert sind, alle erlauben
        if not self.allowed_tenants:
            return True
            
        tenant_id = self._get_tenant_id(turn_context)
        
        if not tenant_id:
            logger.warning("No tenant ID found in request")
            return False
            
        is_allowed = tenant_id in self.allowed_tenants
        
        if not is_allowed:
            logger.warning(f"Tenant {tenant_id} is not in allowed list")
            
        return is_allowed
    
    async def _safe_send_activity(self, turn_context: TurnContext, activity_or_text):
        """
        Safely send an activity with proper error handling
        """
        try:
            # Versuche es mit await
            result = await turn_context.send_activity(activity_or_text)
            return result
        except RuntimeWarning as w:
            # Ignoriere RuntimeWarning für nicht-awaitable Objekte
            if "was never awaited" in str(w):
                logger.debug("Ignoring RuntimeWarning for send_activity")
                return None
            raise
        except Exception as e:
            logger.error(f"Error in send_activity: {e}")
            raise