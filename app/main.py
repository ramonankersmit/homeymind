from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.metrics import router as metrics_router

app = FastAPI(title="HomeyMind")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add metrics endpoint
app.include_router(metrics_router) 