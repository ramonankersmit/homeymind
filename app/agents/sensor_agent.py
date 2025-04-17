"""
Sensor Agent for HomeyMind.

This agent is responsible for reading sensor data from Homey devices.
"""

import asyncio
from typing import Dict, Any
from .base_agent import BaseAgent

class SensorAgent(BaseAgent):
    """Agent that handles sensor data retrieval and processing."""

    def __init__(self, config: Dict[str, Any], mqtt_client):
        """Initialize the sensor agent.
        
        Args:
            config: Configuration dictionary
            mqtt_client: MQTT client for device communication
        """
        super().__init__(config, mqtt_client)
        self.devices = config.get("devices", [])
        self.valid_device_types = {"temperature", "humidity", "motion", "all"}

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process sensor data requests.
        
        Args:
            input_data: Dictionary containing intent data
                {
                    "intent": {
                        "type": "sensor_read",
                        "device_type": "temperature",
                        "zone": "woonkamer"
                    }
                }
            
        Returns:
            Dictionary containing sensor data
        """
        try:
            intent = input_data.get("intent", {})
            device_type = intent.get("device_type")
            zone = intent.get("zone")
            
            if not device_type:
                return {
                    "status": "error",
                    "message": "No device type specified"
                }
            
            if device_type not in self.valid_device_types:
                return {
                    "status": "error",
                    "message": f"Invalid device type. Must be one of: {', '.join(sorted(self.valid_device_types))}"
                }
            
            # Get matching devices
            if device_type == "all":
                devices = [d for d in self.devices if d.get("zone") == zone]
            else:
                devices = [d for d in self.devices if d.get("type") == device_type and d.get("zone") == zone]
            
            if not devices:
                return {
                    "status": "error",
                    "message": f"No {device_type} devices found in zone {zone}"
                }
            
            result = {"status": "success"}
            
            # Get status for each device
            for device in devices:
                device_id = device.get("id")
                device_type = device.get("type")
                
                try:
                    status = await self.mqtt_client.get_status(device_id)
                    if device_type == "all":
                        result[device_type] = status
                    else:
                        result[device_type] = {
                            "value": status.get("value"),
                            "unit": status.get("unit"),
                            "zone": zone,
                            "timestamp": status.get("timestamp")
                        }
                except Exception as e:
                    return {
                        "status": "error",
                        "message": str(e)
                    }
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format.
        
        Returns:
            Current timestamp as ISO string
        """
        from datetime import datetime
        return datetime.now().isoformat() 