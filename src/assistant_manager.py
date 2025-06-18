# src/assistant_manager.py
from openai import OpenAI
import logging
from typing import Dict
import asyncio

logger = logging.getLogger(__name__)

class AssistantManager:
    def __init__(self, api_key: str, assistant_id: str):
        self.client = OpenAI(api_key=api_key)
        self.assistant_id = assistant_id
        self.user_threads: Dict[str, str] = {}
        
    async def get_response(self, user_id: str, message: str) -> str:
        """Get response from OpenAI Assistant for specific user"""
        try:
            # Get or create thread for user
            thread_id = await self._get_user_thread(user_id)
            
            # Add message to thread
            await asyncio.to_thread(
                self.client.beta.threads.messages.create,
                thread_id=thread_id,
                role="user",
                content=message
            )
            
            # Run assistant
            run = await asyncio.to_thread(
                self.client.beta.threads.runs.create,
                thread_id=thread_id,
                assistant_id=self.assistant_id
            )
            
            # Wait for completion
            while run.status in ["queued", "in_progress"]:
                await asyncio.sleep(0.5)
                run = await asyncio.to_thread(
                    self.client.beta.threads.runs.retrieve,
                    thread_id=thread_id,
                    run_id=run.id
                )
            
            if run.status == "completed":
                # Get messages
                messages = await asyncio.to_thread(
                    self.client.beta.threads.messages.list,
                    thread_id=thread_id,
                    limit=1
                )
                
                # Return latest assistant message
                return messages.data[0].content[0].text.value
            else:
                logger.error(f"Run failed with status: {run.status}")
                return "Entschuldigung, es gab einen Fehler bei der Verarbeitung Ihrer Anfrage."
                
        except Exception as e:
            logger.error(f"Error in assistant response: {str(e)}")
            return "Es tut mir leid, ich kann momentan nicht antworten. Bitte versuchen Sie es später erneut."
    
    async def _get_user_thread(self, user_id: str) -> str:
        """Get or create thread for user"""
        if user_id not in self.user_threads:
            thread = await asyncio.to_thread(
                self.client.beta.threads.create
            )
            self.user_threads[user_id] = thread.id
            logger.info(f"Created new thread for user {user_id}: {thread.id}")
        
        return self.user_threads[user_id]