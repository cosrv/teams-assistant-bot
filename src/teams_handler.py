# src/teams_handler.py
from botbuilder.core import TurnContext, ActivityHandler, MessageFactory
from botbuilder.schema import ChannelAccount, Activity, ActivityTypes
import logging
import asyncio

logger = logging.getLogger(__name__)

class TeamsAssistantBot(ActivityHandler):
    def __init__(self, assistant_manager):
        super().__init__()
        self.assistant_manager = assistant_manager
    
    async def on_message_activity(self, turn_context: TurnContext) -> None:
        """Handle incoming messages"""
        # Get user info
        user_id = turn_context.activity.from_property.id
        user_name = turn_context.activity.from_property.name or "User"
        message = turn_context.activity.text
        
        logger.info(f"Message from {user_name} ({user_id}): {message}")
        logger.info(f"Channel ID: {turn_context.activity.channel_id}")
        logger.info(f"Conversation type: {turn_context.activity.conversation.conversation_type}")
        
        # Check if it's a 1:1 conversation (personal chat or webchat)
        is_personal = (
            turn_context.activity.conversation.conversation_type == "personal" or
            turn_context.activity.channel_id == "webchat" or
            turn_context.activity.conversation.conversation_type is None or
            turn_context.activity.conversation.conversation_type == ""
        )
        
        if is_personal:
            try:
                # Show typing indicator
                typing_activity = Activity(
                    type=ActivityTypes.typing,
                    relay_action=True
                )
                await self._safe_send_activity(turn_context, typing_activity)
                
                # Get response from assistant
                response = await self.assistant_manager.get_response(user_id, message)
                
                # Send response using MessageFactory for better compatibility
                await self._safe_send_activity(turn_context, MessageFactory.text(response))
            except Exception as e:
                logger.error(f"Error in message handling: {e}", exc_info=True)
                # Send error message
                await self._safe_send_activity(
                    turn_context, 
                    MessageFactory.text("Entschuldigung, es ist ein Fehler aufgetreten. Bitte versuchen Sie es später erneut.")
                )
        else:
            # Ignore messages in channels/groups
            logger.info("Ignoring message in group conversation")
    
    async def on_members_added_activity(self, members_added: list[ChannelAccount], turn_context: TurnContext) -> None:
        """Welcome new members"""
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                try:
                    # Use MessageFactory for better compatibility
                    welcome_message = MessageFactory.text(
                        "Hallo! Ich bin Ihr persönlicher Assistent. "
                        "Schreiben Sie mir einfach eine direkte Nachricht, und ich helfe Ihnen gerne weiter."
                    )
                    await self._safe_send_activity(turn_context, welcome_message)
                except Exception as e:
                    logger.error(f"Error sending welcome message: {e}", exc_info=True)
    
    async def _safe_send_activity(self, turn_context: TurnContext, activity_or_text):
        """
        Safely send an activity with proper error handling and workaround for await issues
        """
        try:
            # First try the normal way
            result = turn_context.send_activity(activity_or_text)
            
            # Check if result is awaitable
            if asyncio.iscoroutine(result) or asyncio.isfuture(result):
                return await result
            else:
                # If not awaitable, it might already be completed
                return result
        except TypeError as e:
            if "can't be used in 'await' expression" in str(e):
                # Workaround: Try without await
                logger.warning("Applying workaround for non-awaitable send_activity")
                return turn_context.send_activity(activity_or_text)
            else:
                raise e
