# agents.py
import asyncio
import random
from typing import Optional, List, Dict
import re
import requests
import json
import aiohttp  # Use aiohttp for async HTTP requests
from config import TOGETHER_API_KEY
from enum import Enum
from datetime import datetime
import numpy as np
from textblob import TextBlob

class VoiceInputAgent:
    def __init__(self):
        pass  # No initialization needed as we'll use browser's Web Speech API

    async def process(self, audio_stream: bytes) -> Optional[str]:
        # The actual speech recognition happens in the browser
        # This method just receives the text from the browser
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
        self.current_scenario = None
        self.analytics = {
            "sales_skills": {
                "pitch_clarity": 0,
                "objection_handling": 0,
                "active_listening": 0,
                "closing_ability": 0
            },
            "conversation_metrics": [],
            "improvement_areas": set()
        }
        
        # Define sales-specific scenarios
        self.scenarios = {
            "price_negotiation": {
                "context": "Client thinks the product is too expensive",
                "key_points": ["value proposition", "ROI discussion", "budget alignment"]
            },
            "product_demo": {
                "context": "First demo with a potential enterprise client",
                "key_points": ["feature highlights", "use cases", "technical requirements"]
            },
            "objection_handling": {
                "context": "Client has concerns about implementation time",
                "key_points": ["timeline explanation", "resource planning", "support details"]
            }
        }

        self.system_prompt = """
        You are Coachify's AI Sales Coach. Your role is to:
        1. Simulate realistic sales conversations
        2. Challenge the salesperson with common objections
        3. Provide immediate, actionable feedback
        4. Help improve specific sales skills
        5. Maintain a supportive but challenging tone

        Focus on helping the salesperson master high-stakes conversations in a risk-free environment.
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
                You are a startup consultant. Help identify and solve specific business 
                challenges. Focus on actionable solutions.
            """,
            ConversationMode.MARKET_ANALYSIS: """
                You are a market analyst. Analyze market trends and opportunities.
            """,
            ConversationMode.FINANCIAL_PLANNING: """
                You are a financial planner. Help founders plan their financial strategy.
            """,
            ConversationMode.SALES_COACH: """
                You are Coachify's AI Sales Coach. Your role is to:
                1. Simulate realistic sales conversations
                2. Challenge the salesperson with common objections
                3. Provide immediate, actionable feedback
                4. Help improve specific sales skills
                5. Maintain a supportive but challenging tone

                Focus on helping the salesperson master high-stakes conversations in a risk-free environment.
            """,
        }
        self.system_prompt = mode_prompts[new_mode]

    async def process_and_speak(self, transcription: str) -> tuple[str, str]:
        # Add user's message to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": transcription
        })

        # Generate response using Together AI
        response = await self._generate_llm_response()
        
        # Add agent's response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })

        return response, response

    async def _generate_llm_response(self) -> str:
        try:
            # Analyze last response and update skills assessment
            await self._analyze_sales_skills(self.conversation_history[-1]["content"])
            
            context = {
                "scenario": self.current_scenario,
                "skills_assessment": self.analytics["sales_skills"],
                "improvement_areas": list(self.analytics["improvement_areas"])
            }

            async with aiohttp.ClientSession() as session:
                messages = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "system", "content": f"Sales Context: {json.dumps(context)}"}
                ] + self.conversation_history[-2:]

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
                        return data["choices"][0]["message"]["content"]
                    else:
                        return "Let's focus on your value proposition. How would you explain our solution's benefits?"

        except Exception as e:
            print(f"Error: {str(e)}")
            return "Could you rephrase your pitch?"

    async def _analyze_sales_skills(self, text: str):
        """Analyze sales-specific skills from the conversation"""
        # Analyze pitch clarity
        pitch_indicators = ["value", "benefit", "solution", "roi", "results"]
        pitch_clarity = sum(1 for indicator in pitch_indicators if indicator in text.lower()) / len(pitch_indicators)
        
        # Analyze objection handling
        objection_indicators = ["understand", "however", "alternative", "instead", "solution"]
        objection_handling = sum(1 for indicator in objection_indicators if indicator in text.lower()) / len(objection_indicators)
        
        # Analyze active listening
        listening_indicators = ["you mentioned", "you said", "your needs", "you're looking for"]
        active_listening = sum(1 for indicator in listening_indicators if indicator in text.lower()) / len(listening_indicators)
        
        # Analyze closing ability
        closing_indicators = ["next steps", "schedule", "follow up", "agreement", "move forward"]
        closing_ability = sum(1 for indicator in closing_indicators if indicator in text.lower()) / len(closing_indicators)

        # Update analytics
        self.analytics["sales_skills"].update({
            "pitch_clarity": (self.analytics["sales_skills"]["pitch_clarity"] + pitch_clarity) / 2,
            "objection_handling": (self.analytics["sales_skills"]["objection_handling"] + objection_handling) / 2,
            "active_listening": (self.analytics["sales_skills"]["active_listening"] + active_listening) / 2,
            "closing_ability": (self.analytics["sales_skills"]["closing_ability"] + closing_ability) / 2
        })

        # Identify improvement areas
        if pitch_clarity < 0.3: self.analytics["improvement_areas"].add("pitch_clarity")
        if objection_handling < 0.3: self.analytics["improvement_areas"].add("objection_handling")
        if active_listening < 0.3: self.analytics["improvement_areas"].add("active_listening")
        if closing_ability < 0.3: self.analytics["improvement_areas"].add("closing_ability")

    def get_analytics_summary(self) -> Dict:
        """Get a summary of conversation analytics"""
        return {
            "skills_assessment": self.analytics["sales_skills"],
            "improvement_areas": list(self.analytics["improvement_areas"]),
            "conversation_metrics": self.analytics["conversation_metrics"]
        }

    def _extract_business_topics(self, text: str) -> set:
        topics = {
            "funding": ["investment", "funding", "capital", "runway"],
            "market": ["customers", "market", "competition", "demand"],
            "product": ["product", "feature", "development", "technology"],
            "team": ["hiring", "team", "talent", "skills"],
            # Add more topics...
        }
        
        found_topics = set()
        for topic, keywords in topics.items():
            if any(keyword in text.lower() for keyword in keywords):
                found_topics.add(topic)
        return found_topics

    def _update_metrics(self, text: str):
        # Track various metrics
        metrics = {
            "avg_response_length": len(text.split()),
            "question_frequency": text.count("?") / max(1, len(text.split())),
            "technical_terms": self._count_technical_terms(text),
        }
        self.analytics["conversation_metrics"].append(metrics)

class FeedbackAgent:
    @staticmethod
    async def process(conversation_history: list) -> str:
        """Generate sales-specific feedback"""
        try:
            async with aiohttp.ClientSession() as session:
                prompt = f"""
                As a Coachify AI Sales Coach, analyze this sales conversation.
                Focus on:
                1. Pitch effectiveness and clarity
                2. Objection handling technique
                3. Active listening skills
                4. Closing strategy
                
                Provide specific, actionable feedback to improve sales performance.

                Conversation:
                {json.dumps(conversation_history[-2:])}
                """

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
                        "max_tokens": 200
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return "Coach Feedback: " + data["choices"][0]["message"]["content"]
                    else:
                        return "Coach Feedback: Focus on clearly articulating the value proposition."

        except Exception as e:
            print(f"Error in feedback generation: {str(e)}")
            return "Coach Feedback: Remember to address customer needs directly."
