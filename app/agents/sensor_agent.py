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
        super().__init__(config)
        self.mqtt_client = mqtt_client
        self.devices = getattr(config, "devices", {})
        self.valid_device_types = {"temperature", "humidity", "motion", "all"}

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process sensor data request."""
        try:
            intent = input_data.get("intent", {})
            device_type = intent.get("device_type")
            zone = intent.get("zone")
            
            if not device_type:
                return {"status": "error", "error": "No device type specified"}
            
            if device_type not in self.valid_device_types:
                return {"status": "error", "error": f"Invalid device type: {device_type}"}
            
            # Get matching devices
            if device_type == "all":
                devices = [d for d in self.devices.values() if d[0].get("zone") == zone]
            else:
                devices = [d for d in self.devices.values() if d[0].get("type") == device_type and d[0].get("zone") == zone]
            
            if not devices:
                return {"status": "error", "error": f"No {device_type} devices found in zone {zone}"}
            
            result = {"status": "success"}
            
            # Get status for each device
            for device in devices:
                device_id = device[0].get("id")
                device_type = device[0].get("type")
                
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
                    return {"status": "error", "error": str(e)}
            
            return result
            
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def process_sensor_data(self, zone: str) -> Dict[str, Any]:
        """Process sensor data and generate a response."""
        try:
            # Get all sensors in the zone
            zone_devices = self.devices.get(zone, [])
            sensors = [d for d in zone_devices if d.get("type") in ["temperature_sensor", "humidity_sensor", "motion_sensor"]]
            
            if not sensors:
                return {
                    "status": "error",
                    "message": f"Geen sensors gevonden in {zone}",
                    "response": f"Geen sensors gevonden in {zone}"
                }
            
            response = f"Current sensor readings for {zone}:"
            for sensor in sensors:
                sensor_id = sensor.get("id")
                sensor_type = sensor.get("type")
                if sensor_id:
                    try:
                        status = await self.mqtt_client.get_device_status(sensor_id)
                        if status:
                            response += f"\n{sensor_type}: {status.get('value', 'unknown')}"
                    except Exception as e:
                        self._log_message("error", f"Error getting status for sensor {sensor_id}: {str(e)}")
            
            return {
                "status": "success",
                "message": "Sensor data retrieved successfully",
                "response": response
            }
        except Exception as e:
            self._log_message("error", f"Error processing sensor data: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "response": f"Er is een fout opgetreden bij het verwerken van de sensor data: {str(e)}"
            }

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format.
        
        Returns:
            Current timestamp as ISO string
        """
        from datetime import datetime
        return datetime.now().isoformat() 