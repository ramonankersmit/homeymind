from typing import Dict, Any
from .base_agent import BaseAgent
from utils.memory import Memory

class LoggerAgent(BaseAgent):
    """Logs events and actions to memory."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.memory = Memory()
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Log an event or action."""
        event_type = input_data.get("type", "action")
        data = input_data.get("data", {})
        
        try:
            # Add timestamp and agent info
            log_entry = {
                "timestamp": input_data.get("timestamp"),
                "agent": input_data.get("agent"),
                "type": event_type,
                "data": data
            }
            
            # Store in memory
            self.memory.add_event(log_entry)
            
            self.log(f"Logged {event_type} event")
            return {"status": "success", "event": log_entry}
            
        except Exception as e:
            self.log(f"Error logging event: {str(e)}")
            return {"status": "error", "message": str(e)} 