"""
Sensor Agent for HomeyMind.

This agent is responsible for reading sensor data from Homey devices.
"""

from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent

class SensorAgent(BaseAgent):
    """Agent that handles sensor data retrieval and processing."""

    def __init__(self, config: Dict[str, Any], mqtt_client):
        """Initialize the sensor agent.
        
        Args:
            config: Configuration dictionary
            mqtt_client: MQTT client for device communication
        """
        super().__init__(config, mqtt_client)
        self.sensor_types = ["temperature", "humidity", "motion", "contact"]

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process sensor data requests.
        
        Args:
            input_data: Dictionary containing sensor request details
                {
                    "device_type": "temperature",
                    "zone": "woonkamer"
                }
            
        Returns:
            Dictionary containing sensor data and status
        """
        device_type = input_data.get("device_type")
        zone = input_data.get("zone", "woonkamer")

        if not device_type or device_type not in self.sensor_types:
            return {
                "status": "error",
                "error": f"Invalid sensor type. Must be one of: {', '.join(self.sensor_types)}"
            }

        try:
            # Get sensor data from MQTT
            sensor_data = await self.get_device_status(zone, device_type)
            
            return {
                "status": "success",
                "sensor_data": {
                    "type": device_type,
                    "zone": zone,
                    "value": sensor_data,
                    "timestamp": self._get_timestamp()
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to get sensor data: {str(e)}"
            }

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format.
        
        Returns:
            Current timestamp as ISO string
        """
        from datetime import datetime
        return datetime.now().isoformat() 