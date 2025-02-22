# main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import Dict

from agents import VoiceInputAgent, ConversationSimulatorAgent, FeedbackAgent
from database import init_db, save_conversation

# Import user routes (adjust the import path as needed)
from routes import users,authentication

app = FastAPI()


# Include your user (and any other) routes
app.include_router(authentication.router)
app.include_router(users.router)





# Store active connections
connections: Dict[str, WebSocket] = {}

@app.on_event("startup")
async def startup():
    # Initialize the database
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
    user_id = "default_user"  # Replace with actual user identification logic
    
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
                
                # Save conversation log
                await save_conversation(user_id=user_id, transcript=transcription, analysis=feedback)
                
                # Send response back to client
                await websocket.send_json({
                    "transcription": transcription,
                    "response_text": response_text,
                    "feedback": feedback
                })
                
                # Send audio response if available
                if audio_response:
                    await websocket.send_bytes(audio_response)
                
    except WebSocketDisconnect:
        print("Client disconnected")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
