import azure.cognitiveservices.speech as speechsdk
import os
from dotenv import load_dotenv

load_dotenv()

def test_azure_speech():
    # Get credentials from .env
    speech_key = os.getenv('AZURE_SPEECH_KEY')
    speech_region = os.getenv('AZURE_SPEECH_REGION').strip().rstrip('\\')
    
    print(f"Testing Azure Speech with:")
    print(f"Region: {speech_region}")
    print(f"Key: {speech_key[:5]}...")  # Print first 5 chars for verification
    
    try:
        # Initialize speech config
        speech_config = speechsdk.SpeechConfig(
            subscription=speech_key,
            region=speech_region
        )
        
        # Test text-to-speech
        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
        result = speech_synthesizer.speak_text_async("This is a test of Azure Speech Services.").get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print("Text-to-speech test successful!")
        else:
            print(f"Text-to-speech failed: {result.reason}")
            
    except Exception as e:
        print(f"Error testing Azure Speech: {str(e)}")

if __name__ == "__main__":
    test_azure_speech() 