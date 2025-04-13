from typing import Dict, Any, Optional
from .base_agent import BaseAgent
from homey.mqtt_client import MQTTClient
from utils.intent_parser import parse_intent
from utils.device_list import get_device_status

class CoordinatorAgent(BaseAgent):
    """Coordinates between different agents and handles user approval."""
    
    def __init__(self, config: Dict[str, Any], mqtt_client: MQTTClient):
        super().__init__(config)
        self.mqtt_client = mqtt_client
        self.auto_approval_rules = config.get("auto_approval", [])
    
    async def process(self, input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process the input data and coordinate between agents."""
        # Extract intent from user input
        intent = await self._get_intent(input_data["text"])
        if not intent:
            self.log("Could not determine intent")
            return None
        
        # Get current device status
        status = await self._get_device_status(intent)
        
        # Generate action proposal
        proposal = await self._generate_proposal(intent, status)
        if not proposal:
            self.log("Could not generate proposal")
            return None
        
        # Check if action can be auto-approved
        if self._can_auto_approve(proposal):
            self.log(f"Auto-approving action: {proposal['action']}")
            return await self._execute_action(proposal)
        
        # Ask for user approval
        approval = await self._get_approval(proposal)
        if approval:
            return await self._execute_action(proposal)
        
        self.log("Action was not approved")
        return None
    
    async def _get_intent(self, text: str) -> Optional[Dict[str, Any]]:
        """Get the intent from the user's input."""
        return parse_intent(text)
    
    async def _get_device_status(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Get the current status of relevant devices."""
        return get_device_status(intent.get("device"))
    
    async def _generate_proposal(self, intent: Dict[str, Any], status: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate an action proposal based on intent and current status."""
        # This will be implemented by the PlannerAgent
        return {
            "action": "set_temperature",
            "device": "thermostat",
            "value": 20,
            "reason": "Temperature is below comfort level"
        }
    
    def _can_auto_approve(self, proposal: Dict[str, Any]) -> bool:
        """Check if the action can be auto-approved based on rules."""
        for rule in self.auto_approval_rules:
            if (rule["apparaat"] == proposal["device"] and 
                rule["actie"] == proposal["action"]):
                return True
        return False
    
    async def _get_approval(self, proposal: Dict[str, Any]) -> bool:
        """Get user approval for the proposed action."""
        # For now, just print the proposal
        print(f"Voorstel: {proposal['action']} voor {proposal['device']}")
        print("Wil je dit doen? (ja/nee)")
        response = input().lower()
        return response in ["ja", "yes", "y"]
    
    async def _execute_action(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the approved action."""
        self.log(f"Executing action: {proposal['action']}")
        # This will be implemented by the HomeyAgent
        return {"status": "success", "action": proposal} 