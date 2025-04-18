"""
Sensor Agent for HomeyMind.

This agent is responsible for reading sensor data from Homey devices.
"""

import asyncio
from typing import Dict, Any
from .base_agent import BaseAgent
from .tool_registry import register_tool, Tool
from .schemas import SensorDataInput, SensorDataOutput, AllSensorsInput, AllSensorsOutput

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
        
        # Register tools
        register_tool(Tool(
            name="get_sensor_data",
            func=self.process,
            input_model=SensorDataInput,
            output_model=SensorDataOutput,
            description="Read sensor values for a given zone"
        ))
        
        register_tool(Tool(
            name="get_all_sensors",
            func=self.process_sensor_data,
            input_model=AllSensorsInput,
            output_model=AllSensorsOutput,
            description="Read all sensors in a given zone"
        ))

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process sensor data request."""
        try:
            intent = input_data.get("intent", {})
            device_type = intent.get("device_type")
            zone = intent.get("zone")
            
            if not device_type:
                return {
                    "status": "error",
                    "message": "No device type specified",
                    "error": "No device type specified"
                }
            
            # Map device types to sensor types
            device_type_map = {
                "temperature": "temperature_sensor",
                "humidity": "humidity_sensor",
                "motion": "motion_sensor"
            }
            
            sensor_type = device_type_map.get(device_type)
            if not sensor_type and device_type != "all":
                return {
                    "status": "error",
                    "message": f"Invalid device type: {device_type}",
                    "error": f"Invalid device type: {device_type}"
                }
            
            # Get matching devices
            if device_type == "all":
                devices = [d for d in self.devices.values() if d[0].get("zone") == zone]
            else:
                devices = [d for d in self.devices.values() if d[0].get("type") == sensor_type and d[0].get("zone") == zone]
            
            if not devices:
                return {
                    "status": "error",
                    "message": f"No {device_type} devices found in zone {zone}",
                    "error": f"No {device_type} devices found in zone {zone}"
                }
            
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
                        result[device_type.replace("_sensor", "")] = {
                            "value": status.get("value"),
                            "unit": status.get("unit"),
                            "zone": zone,
                            "timestamp": status.get("timestamp")
                        }
                except Exception as e:
                    return {
                        "status": "error",
                        "message": str(e),
                        "error": str(e)
                    }
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "error": str(e)
            }

    async def process_sensor_data(self, sensor_id: str, value: float = None) -> Dict[str, Any]:
        """Process sensor data and generate a response."""
        try:
            if value is None:
                # Get all sensors in the zone
                zone_devices = self.devices.get(sensor_id, [])
                sensors = [d for d in zone_devices if d.get("type") in ["temperature_sensor", "humidity_sensor", "motion_sensor"]]
                
                if not sensors:
                    return {
                        "status": "error",
                        "message": f"Geen sensors gevonden in {sensor_id}",
                        "response": f"Geen sensors gevonden in {sensor_id}"
                    }
                
                response = f"Current sensor readings for {sensor_id}:"
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
            else:
                # Get sensor info from devices dictionary
                sensor_info = None
                for devices in self.devices.values():
                    for device in devices:
                        if device.get("id") == sensor_id:
                            sensor_info = device
                            break
                    if sensor_info:
                        break
                
                if not sensor_info:
                    # Accept unknown sensors with their value
                    return f"Sensor {sensor_id} heeft waarde {value}."
                
                sensor_type = sensor_info.get("type", "unknown")
                zone = sensor_info.get("zone", "unknown")
                
                # Generate response based on sensor type
                if "temperature" in sensor_type.lower():
                    response = f"De temperatuur in de {zone} is {value} graden Celsius."
                elif "humidity" in sensor_type.lower():
                    response = f"De luchtvochtigheid in de {zone} is {value}%."
                elif "motion" in sensor_type.lower():
                    response = f"Er is beweging gedetecteerd in de {zone}."
                else:
                    response = f"Sensor {sensor_id} heeft waarde {value}."
                
                self._log_message("info", f"Processed sensor data: {response}")
                return response
        except Exception as e:
            self._log_message("error", f"Error processing sensor data: {str(e)}")
            return f"Er is een fout opgetreden bij het verwerken van de sensor data: {str(e)}"

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format.
        
        Returns:
            Current timestamp as ISO string
        """
        from datetime import datetime
        return datetime.now().isoformat() 