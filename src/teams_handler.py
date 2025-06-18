# src/teams_handler.py
from botbuilder.core import TurnContext, ActivityHandler
from botbuilder.schema import ChannelAccount
import logging

logger = logging.getLogger(__name__)

class TeamsAssistantBot(ActivityHandler):
    def __init__(self, assistant_manager):
        super().__init__()
        self.assistant_manager = assistant_manager
    
    async def on_message_activity(self, turn_context: TurnContext) -> None:
        """Handle incoming messages"""
        # Get user info
        user_id = turn_context.activity.from_property.id
        user_name = turn_context.activity.from_property.name
        message = turn_context.activity.text
        
        logger.info(f"Message from {user_name} ({user_id}): {message}")
        
        # Only respond in 1:1 conversations
        if turn_context.activity.conversation.conversation_type == "personal":
            # Show typing indicator
            await turn_context.send_activity({"type": "typing"})
            
            # Get response from assistant
            response = await self.assistant_manager.get_response(user_id, message)
            
            # Send response
            await turn_context.send_activity(response)
        else:
            # Ignore messages in channels/groups
            logger.info("Ignoring message in group conversation")
    
    async def on_members_added_activity(self, members_added: list[ChannelAccount], turn_context: TurnContext) -> None:
        """Welcome new members"""
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    "Hallo! Ich bin Ihr persönlicher Assistent. "
                    "Schreiben Sie mir einfach eine direkte Nachricht, und ich helfe Ihnen gerne weiter."
                )