from fastapi import APIRouter, WebSocket, Depends, HTTPException, UploadFile, File, Request
import azure.cognitiveservices.speech as speechsdk
import asyncio
import json
import os
from dotenv import load_dotenv
import requests
from datetime import datetime
from textblob import TextBlob  # for sentiment analysis
import random
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from .oauth2 import get_current_user

# Load environment variables
load_dotenv()

router = APIRouter(
    prefix="/voice",
    tags=["Voice"]
)

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")


# ---------------------------
# IBM Watsonx Integration Code
# ---------------------------
def run_watson_sales_coach(user_input: str):
    from ibm_watsonx_ai import Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference
    from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
    from ibm_watsonx_ai.foundation_models.utils.enums import DecodingMethods

    # Set up generation parameters
    gen_params = {
        GenParams.DECODING_METHOD: DecodingMethods.GREEDY,
        GenParams.TEMPERATURE: 0.8,
        GenParams.MIN_NEW_TOKENS: 10,
        GenParams.MAX_NEW_TOKENS: 1024
    }

    # Initialize the model inference with IBM Watsonx credentials
    model_inference = ModelInference(
        model_id="mistralai/mixtral-8x7b-instruct-v01",  # Ensure this is correct
        params=gen_params,
        credentials=Credentials(
            api_key="0YivQ4fK01hPbj2SBso-XKuovHb7ARTBxTuNSZRmHizG",
            url="https://us-south.ml.cloud.ibm.com"
        ),
        project_id="ecf3764f-9871-4ef0-bc8b-4899f482e977"
    )
    
    # Define a system prompt appropriate for a sales coach
    system_prompt = ("You are a sales coach helping startups perfect their pitch. "
                     "Ask one challenging question about their value proposition, target market, or competitive advantage. "
                     "Keep your response short and focused.")
    
    complete_prompt = f"{system_prompt}\n\nUser: {user_input}"
    
    response = model_inference.generate(complete_prompt)
    results = response.get('results', [])
    del model_inference
    # Extract generated text from each result
    generated_texts = [item.get('generated_text') for item in results if item.get('generated_text')]
    return generated_texts

# ---------------------------
# ModernSalesTrainer using IBM Watsonx
# ---------------------------
class ModernSalesTrainer:
    def __init__(self):
        # No need for Together API key anymore.
        pass

    async def get_response(self, user_input: str) -> str:
        # Run the IBM Watsonx integration function in an executor since it is synchronous.
        loop = asyncio.get_running_loop()
        generated_texts = await loop.run_in_executor(None, run_watson_sales_coach, user_input)
        if generated_texts and len(generated_texts) > 0:
            return generated_texts[0].strip()
        else:
            return "How can you differentiate your solution from competitors?"

# ---------------------------
# Voice Chat Endpoint
# ---------------------------
@router.websocket("/chat")
async def voice_chat(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connected")
    
    try:
        # Initialize Azure Speech configuration for synthesis and recognition.
        speech_config = speechsdk.SpeechConfig(
            subscription=os.getenv("AZURE_SPEECH_KEY"),
            region=os.getenv("AZURE_SPEECH_REGION")
        )
        
        trainer = ModernSalesTrainer()
        is_speaking = False
        loop = asyncio.get_running_loop()
        speech_lock = asyncio.Lock()

        async def handle_speech_synthesis(text: str):
            nonlocal is_speaking, speech_synthesizer
            try:
                async with speech_lock:
                    is_speaking = True
                    result = speech_synthesizer.speak_text_async(text).get()
                    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                        audio_data = result.audio_data
                        await websocket.send_bytes(audio_data)
                    is_speaking = False
            except Exception as e:
                print(f"Speech synthesis error: {e}")
                is_speaking = False

        async def handle_recognition(text: str):
            nonlocal is_speaking
            try:
                if is_speaking:
                    speech_synthesizer.stop_speaking_async().get()
                    await asyncio.sleep(0.2)
                    is_speaking = False
                    return
                # Process new input if not currently synthesizing speech.
                response = await trainer.get_response(text)
                print(f"Generated response: {response}")
                if response:
                    await handle_speech_synthesis(response)
            except Exception as e:
                print(f"Recognition handling error: {e}")

        def handle_speech_recognized(evt):
            if evt.result.text:
                print(f"Recognized: {evt.result.text}")
                asyncio.run_coroutine_threadsafe(
                    handle_recognition(evt.result.text),
                    loop
                )

        # Configure the Azure speech synthesis parameters.
        speech_config.speech_synthesis_voice_name = "en-US-GuyNeural"
        speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio24Khz48KBitRateMonoMp3
        )
        
        speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=None
        )
        
        # Configure the speech recognizer to use the default microphone.
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config
        )
        speech_recognizer.recognized.connect(handle_speech_recognized)
        
        # Send an initial greeting.
        initial_message = "I am the IT Director evaluating your proposal. Convince me why I should trust your solution with our sensitive data."
        await handle_speech_synthesis(initial_message)
        
        speech_recognizer.start_continuous_recognition()
        print("Ready for conversation")

        while True:
            try:
                message = await websocket.receive_text()
                if message == "stop":
                    break
                elif message == "interrupt" and is_speaking:
                    speech_synthesizer.stop_speaking_async()
            except Exception as e:
                print(f"WebSocket error: {e}")
                break

    except Exception as e:
        print(f"Error in voice chat: {e}")
    
    finally:
        if is_speaking:
            speech_synthesizer.stop_speaking_async()
        speech_recognizer.stop_continuous_recognition()
        await websocket.close()

@router.post("/process")
async def process_voice(
    audio: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Process the audio file (this is a placeholder)
        return {
            "success": True,
            "text_response": "Voice processing endpoint is working"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
