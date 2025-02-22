import asyncio
import aiohttp
import logging
from datetime import datetime

async def test_elevenlabs_tts(text: str) -> str:
    voice_id = "21m00Tcm4TlvDq8ikWAM"  # Example voice ID
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": "sk_541e08bfcd7ce5ef3ce9361153d908c7d1a06725c5704c41",
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                audio_bytes = await response.read()
                filename = f"test_output_{datetime.utcnow().timestamp()}.mp3"
                with open(filename, "wb") as f:
                    f.write(audio_bytes)
                print(f"Test succeeded! Audio saved as {filename}")
                return filename
            else:
                error_text = await response.text()
                logging.error(f"ElevenLabs TTS API error: {response.status} - {error_text}")
                raise Exception(f"ElevenLabs API error: {response.status}")

# Run the test
asyncio.run(test_elevenlabs_tts("Hello world, this is a test message."))
