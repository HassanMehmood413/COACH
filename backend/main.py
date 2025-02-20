# main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import asyncio
from typing import Dict

from agents import VoiceInputAgent, ConversationSimulatorAgent, FeedbackAgent
from database import init_db, save_conversation

app = FastAPI()

# Mount static assets if needed (for CSS/JS)
# app.mount("/static", StaticFiles(directory="static"), name="static")

# Store active connections
connections: Dict[str, WebSocket] = {}

@app.on_event("startup")
async def startup():
    # Initialize NeonDatabase
    await init_db()

@app.get("/")
async def get():
    # Serve the basic HTML client
    with open("templates/index.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)

@app.websocket("/ws/voice")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Initialize agents
    voice_input_agent = VoiceInputAgent()
    conversation_agent = ConversationSimulatorAgent()
    feedback_agent = FeedbackAgent()
    
    conversation_history = []
    
    try:
        while True:
            # Receive audio stream from client
            audio_chunk = await websocket.receive_bytes()
            
            # Process speech to text
            transcription = await voice_input_agent.process(audio_chunk)
            
            if transcription:
                # Add to conversation history
                conversation_history.append({"role": "user", "message": transcription})
                
                # Generate and speak response
                response_text, audio_response = await conversation_agent.process_and_speak(transcription)
                conversation_history.append({"role": "agent", "message": response_text})
                
                # Generate feedback
                feedback = await feedback_agent.process(conversation_history)
                
                # Send response back to client
                await websocket.send_json({
                    "transcription": transcription,
                    "response_text": response_text,
                    "feedback": feedback
                })
                
                # Send audio response
                if audio_response:
                    await websocket.send_bytes(audio_response)
                
    except WebSocketDisconnect:
        print("Client disconnected")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
