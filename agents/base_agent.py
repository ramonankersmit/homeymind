from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseAgent(ABC):
    """Base class for all agents in the HomeyMind system."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__
    
    @abstractmethod
    async def process(self, input_data: Any) -> Any:
        """Process the input data and return the result."""
        pass
    
    def log(self, message: str, level: str = "info"):
        """Log a message with the agent's name."""
        print(f"[{self.name}] {message}") 