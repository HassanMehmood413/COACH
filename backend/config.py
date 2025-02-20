# config.py
import os

# Connection string for NeonDatabase (PostgreSQL)
DATABASE_URL = os.getenv('DATABASE_URL')

# LLM API configuration
TOGETHER_API_KEY = os.getenv('TOGETHER_API_KEY')  # or use your preferred LLM provider

# No API keys needed as we're using Web Speech API
