import asyncio
import json
import logging
from sse_starlette.sse import EventSourceResponse
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/test_backend")
async def test_backend(request: Request):
    """Test backend by sending updates every second."""
    async def event_generator():
        # Send initial connection message
        yield {
            "event": "open",
            "id": "0",
            "data": json.dumps({"status": "connected"})
        }
        
        # Send a series of agent messages
        messages = [
            {"role": "planner", "message": "Parsing intent: test message", "agent": "IntentParser", "timestamp": None},
            {"role": "planner", "message": "Intent: Test message", "agent": "IntentParser", "timestamp": None},
            {"role": "user", "message": "Processing request: test message", "agent": "HomeyAssistant", "timestamp": None},
            {"role": "assistant", "message": "I'll help you with that.", "agent": "HomeyAssistant", "timestamp": None},
            {"role": "executor", "message": "Executing command: test message", "agent": "DeviceController", "timestamp": None},
            {"role": "executor", "message": "Command executed successfully.", "agent": "DeviceController", "timestamp": None}
        ]
        
        for i, msg in enumerate(messages):
            if await request.is_disconnected():
                break
                
            # Simulate processing
            await asyncio.sleep(1)
            
            logger.debug(f"Sending agent message: {msg}")
            
            yield {
                "event": "agent_message",
                "id": str(i),
                "data": json.dumps({
                    "type": "subagent",
                    "message": msg["message"],
                    "role": msg["role"],
                    "timestamp": msg["timestamp"]
                })
            }
        
        # Send completion message
        yield {
            "event": "complete",
            "id": str(len(messages)),
            "data": json.dumps({
                "response": "Test completed successfully!",
                "agent_data": {
                    "conversations": messages
                }
            })
        }
    
    return EventSourceResponse(event_generator()) 