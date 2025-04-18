from pydantic import BaseModel, Field

class OpenAIConfig(BaseModel):
    model: str = Field(..., description="OpenAI model name")
    api_type: str = Field("openai", description="API type")
    api_key: str = Field(..., description="OpenAI API key")

class LLMConfig(BaseModel):
    name: str = Field(..., description="Name of the agent")
    openai: OpenAIConfig = Field(..., description="OpenAI configuration") 