import pytest
import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient
import asyncio
import json
import logging
from sse_starlette.sse import EventSourceResponse
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from httpx import ASGITransport

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
            await asyncio.sleep(0.1)  # Reduced sleep time for testing
            
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

@pytest.fixture
def test_app():
    return app

@pytest.mark.asyncio
async def test_backend(test_app):
    """Test the backend SSE stream endpoint."""
    transport = ASGITransport(app=test_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        async with client.stream("GET", "/test_backend") as response:
            assert response.status_code == 200
            
            # Read all events
            lines = []
            async for line in response.aiter_lines():
                if line.strip():  # Skip empty lines
                    lines.append(line)
                if "event: complete" in line:
                    break
            
            # Check initial connection event
            assert "event: open" in lines[0]
            data = json.loads(lines[1].replace("data: ", ""))
            assert data["status"] == "connected"
            
            # Check agent messages
            current_line = 2
            for i in range(6):  # We know there are 6 messages
                assert "event: agent_message" in lines[current_line]
                data = json.loads(lines[current_line + 1].replace("data: ", ""))
                assert "type" in data
                assert "message" in data
                assert "role" in data
                current_line += 2
            
            # Check completion event
            assert "event: complete" in lines[-2]
            data = json.loads(lines[-1].replace("data: ", ""))
            assert data["response"] == "Test completed successfully!"
            assert "agent_data" in data
            assert len(data["agent_data"]["conversations"]) == 6 