from typing import Dict, Any
from .base_agent import BaseAgent
from homey.mqtt_client import MQTTClient

class HomeyAgent(BaseAgent):
    """Executes actions via MQTT to control Homey devices."""
    
    def __init__(self, config: Dict[str, Any], mqtt_client: MQTTClient):
        super().__init__(config)
        self.mqtt_client = mqtt_client
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an action via MQTT."""
        action = input_data.get("action")
        device = input_data.get("device")
        value = input_data.get("value")
        
        if not action or not device:
            self.log("Missing action or device")
            return {"status": "error", "message": "Missing action or device"}
        
        try:
            # Construct MQTT topic and payload
            topic = f"{self.config['mqtt']['topic_prefix']}{device}/{action}"
            payload = {"value": value} if value is not None else {}
            
            # Publish to MQTT
            self.mqtt_client.publish(topic, payload)
            
            self.log(f"Executed {action} on {device}")
            return {"status": "success", "action": action, "device": device}
            
        except Exception as e:
            self.log(f"Error executing action: {str(e)}")
            return {"status": "error", "message": str(e)} 