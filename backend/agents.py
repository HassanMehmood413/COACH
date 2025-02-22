import asyncio
import random
import json
import aiohttp  # Use aiohttp for async HTTP requests
import logging
from typing import Optional, List, Dict
from enum import Enum
from datetime import datetime
import numpy as np
from config import TOGETHER_API_KEY
from textblob import TextBlob

# Import the save_conversation function
from database import save_conversation

# Configure logging
logging.basicConfig(level=logging.INFO)


class VoiceInputAgent:
    def __init__(self):
        pass  # No initialization needed as we'll use the browser's Web Speech API

    async def process(self, audio_stream: bytes) -> Optional[str]:
        # The actual speech recognition happens in the browser.
        # This method decodes the audio stream to text.
        return audio_stream.decode('utf-8')


class ConversationMode(Enum):
    PITCH_PRACTICE = "pitch_practice"
    INVESTOR_SIMULATION = "investor_simulation"
    PROBLEM_SOLVING = "problem_solving"
    MARKET_ANALYSIS = "market_analysis"
    FINANCIAL_PLANNING = "financial_planning"
    SALES_COACH = "sales_coach"


class ConversationSimulatorAgent:
    def __init__(self):
        self.conversation_history = []
        self.mode = ConversationMode.SALES_COACH
        self.analytics = {
            "sales_skills": {
                "pitch_clarity": 0,
                "objection_handling": 0,
                "active_listening": 0,
                "closing_ability": 0
            },
            "improvement_areas": set()
        }
        
        # System prompt instructing the model to return only the final answer.
        self.system_prompt = """
        You are Coachify's AI Sales Coach. Your role is to:
        1. Simulate realistic sales conversations.
        2. Challenge the salesperson with common objections.
        3. Provide immediate, actionable feedback.
        4. Help improve specific sales skills.
        5. Maintain a supportive but challenging tone.
        
        Provide only the final answer without showing your internal reasoning.
        """

    async def switch_mode(self, new_mode: ConversationMode):
        self.mode = new_mode
        mode_prompts = {
            ConversationMode.PITCH_PRACTICE: """
                You are a pitch coach. Focus on clarity, value proposition, and delivery.
                Help founders perfect their elevator pitch in 3-5 clear sentences.
            """,
            ConversationMode.INVESTOR_SIMULATION: """
                You are a VC investor. Ask tough questions about market size, growth strategy,
                and financial projections. Be direct but constructive.
            """,
            ConversationMode.PROBLEM_SOLVING: """
                You are a startup consultant. Help identify and solve specific business challenges.
                Focus on actionable solutions.
            """,
            ConversationMode.MARKET_ANALYSIS: """
                You are a market analyst. Analyze market trends and opportunities.
            """,
            ConversationMode.FINANCIAL_PLANNING: """
                You are a financial planner. Help founders plan their financial strategy.
            """,
            ConversationMode.SALES_COACH: self.system_prompt,
        }
        self.system_prompt = mode_prompts[new_mode]

    async def process_and_speak(self, transcription: str) -> tuple[str, str]:
        """
        Processes user input and generates a response.
        Returns a tuple: (final_response_text, audio_response).
        Currently, audio_response is an empty string.
        """
        # Append the user's message to conversation history.
        self.conversation_history.append({
            "role": "user",
            "content": transcription
        })

        # Generate the response using the LLM.
        response = await self._generate_llm_response()

        # Append the assistant's response to conversation history.
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })

        # Save conversation to the database.
        await save_conversation(user_id="default_user", transcript=transcription, analysis=response)

        # Return a tuple (response, audio_response).
        return response, ""

    async def _generate_llm_response(self) -> str:
        """Generates response using Together AI API."""
        try:
            last_user_input = self.conversation_history[-1]["content"]

            # Prepare the messages payload.
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": last_user_input}
            ]
            
            logging.info(f"Sending messages to LLM: {messages}")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.together.xyz/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {TOGETHER_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 150
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        final_answer = data["choices"][0]["message"]["content"].strip()
                        logging.info(f"LLM Response: {final_answer}")
                        return final_answer
                    else:
                        error_text = await response.text()
                        logging.error(f"LLM Error: {response.status} - {error_text}")
                        return "I'm sorry, I encountered an error. Could you please try again?"
        except Exception as e:
            logging.error(f"Exception in _generate_llm_response: {str(e)}")
            return "An error occurred while processing your request."

    def get_analytics_summary(self) -> Dict:
        """Returns a summary of conversation analytics."""
        return {
            "sales_skills": self.analytics["sales_skills"],
            "improvement_areas": list(self.analytics["improvement_areas"])
        }


class FeedbackAgent:
    @staticmethod
    async def process(conversation_history: List[Dict]) -> str:
        """Generates concise feedback based on conversation history."""
        try:
            last_message = conversation_history[-1]["content"]
            if "business model" in last_message.lower():
                return "Great, your business model shows promise. Could you elaborate on your revenue streams?"
            elif "strategy" in last_message.lower():
                return "Focusing on your target market is key. Consider highlighting your competitive advantages."

            async with aiohttp.ClientSession() as session:
                prompt = f"Provide concise feedback for the following conversation: {json.dumps(conversation_history[-2:])}"
                async with session.post(
                    "https://api.together.xyz/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {TOGETHER_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": 50
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        feedback = data["choices"][0]["message"]["content"].strip()
                        return f"Feedback: {feedback}"
                    else:
                        logging.error(f"Feedback LLM Error: {response.status} - {await response.text()}")
                        return "Feedback: Please keep your points clear and concise."
        except Exception as e:
            logging.error(f"Feedback generation error: {str(e)}")
            return "Feedback: Please ensure your communication is clear."


# End of agents.py
