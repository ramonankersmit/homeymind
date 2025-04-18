from typing import List, Dict, Any
from pydantic import BaseModel, Field


class Device(BaseModel):
    """Device configuration."""
    id: str = Field(..., description="Device ID")
    type: str = Field(..., description="Device type")
    zone: str = Field(..., description="Device zone")


class OpenAIConfig(BaseModel):
    """OpenAI configuration."""
    model: str = Field(..., description="OpenAI model name")
    api_type: str = Field("openai", description="API type")
    api_key: str = Field(..., description="OpenAI API key")
    devices: List[Device] = Field(default_factory=list, description="List of devices")


class LLMConfig(BaseModel):
    """Configuration for LLM-based agents."""
    name: str
    openai: OpenAIConfig
    mqtt_config: Dict[str, Any] = Field(default_factory=dict)
    tts_config: Dict[str, Any] = Field(default_factory=dict)
    llm_config: Dict[str, Any] = Field(default_factory=dict)
    require_confirmation: bool = True
    devices: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    speakers: List[Dict[str, Any]] = Field(default_factory=list)
    default_volume: int = 50
    default_zone: str = "all"

    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True
        extra = "allow" 