from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
import logging

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
            await asyncio.sleep(1)
            
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