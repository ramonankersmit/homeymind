import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from app.agents.autogen_manager import AutoGenManager
import yaml

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "HomeyMind API"}

# Load configuration
with open(project_root / "config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Initialize AutoGen manager
autogen_manager = AutoGenManager(config)

@app.get("/chat")
async def chat(request: Request, message: str):
    async def event_generator():
        try:
            async for msg in autogen_manager.process_intent_streaming({"text": message}):
                if msg.get("type") == "complete":
                    yield {
                        "event": "complete",
                        "data": json.dumps({
                            "status": "success",
                            "response": msg.get("response", "")
                        })
                    }
                else:
                    yield {
                        "event": "agent_message",
                        "data": json.dumps(msg)
                    }
        except Exception as e:
            # Fallback for errors
            err = {
                "message": f"Er is een fout opgetreden: {str(e)}",
                "role": "agent",
                "isError": True,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
            yield {"event": "agent_message", "data": json.dumps(err)}
            yield {
                "event": "complete", 
                "data": json.dumps({
                    "status": "error",
                    "error": str(e)
                })
            }
    
    return EventSourceResponse(event_generator())