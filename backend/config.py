# config.py
import os
from dotenv import load_dotenv


load_dotenv()

# Connection string for NeonDatabase (PostgreSQL)
DATABASE_URL = os.getenv('DATABASE_URL')

# LLM API configuration
TOGETHER_API_KEY = os.getenv('TOGETHER_API_KEY') 
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')

# No API keys needed as we're using Web Speech API
