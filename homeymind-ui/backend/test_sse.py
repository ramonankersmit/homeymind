from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
import logging
import pytest
import httpx
from fastapi.testclient import TestClient
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

@app.get("/test")
async def test_stream(request: Request, message: str):
    """Test SSE by sending updates every second."""
    async def event_generator():
        # Split message into words
        words = message.split()
        
        # Send initial connection message
        yield {
            "event": "open",
            "data": "Connected to SSE stream"
        }
        
        # Process one word per second
        for i, word in enumerate(words, 1):
            if await request.is_disconnected():
                break
                
            # Simulate processing
            await asyncio.sleep(0.1)  # Reduced sleep time for testing
            
            data = {
                "message": f"Processing word {i}: {word}",
                "progress": i / len(words) * 100
            }
            
            logger.debug(f"Sending update: {data}")
            
            yield {
                "event": "update",
                "data": json.dumps(data)
            }
        
        # Send completion message
        yield {
            "event": "complete",
            "data": json.dumps({
                "message": "Processing complete!",
                "final_text": message.upper()
            })
        }
    
    return EventSourceResponse(event_generator())

@pytest.fixture
def test_app():
    return app

@pytest.mark.asyncio
async def test_stream(test_app):
    """Test the SSE stream endpoint."""
    transport = ASGITransport(app=test_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        async with client.stream("GET", "/test?message=hello world") as response:
            assert response.status_code == 200
            
            # Read the first event (connection)
            lines = []
            async for line in response.aiter_lines():
                if line.strip():  # Skip empty lines
                    lines.append(line)
                if "event: complete" in line:
                    break
            
            # Check initial connection event
            assert "event: open" in lines[0]
            assert "data: Connected to SSE stream" in lines[1]
            
            # Check word processing events
            current_line = 2
            for i, word in enumerate(["hello", "world"], 1):
                assert "event: update" in lines[current_line]
                data = json.loads(lines[current_line + 1].replace("data: ", ""))
                assert data["message"] == f"Processing word {i}: {word}"
                assert data["progress"] == (i / 2 * 100)
                current_line += 2
            
            # Check completion event
            assert "event: complete" in lines[-2]
            data = json.loads(lines[-1].replace("data: ", ""))
            assert data["message"] == "Processing complete!"
            assert data["final_text"] == "HELLO WORLD" 