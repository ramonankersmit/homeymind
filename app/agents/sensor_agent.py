"""
Sensor Agent for HomeyMind.

This agent is responsible for reading sensor data from Homey devices.
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent

class SensorAgent(BaseAgent):
    """Agent for reading sensor data from devices."""

    async def process(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process sensor reading requests.
        
        Args:
            intent (Dict[str, Any]): Intent data containing device information
            
        Returns:
            Dict[str, Any]: Sensor readings including temperatures, humidity, etc.
        """
        # Get device configuration
        devices = self.config.get("devices", [])
        
        # Initialize result structure
        result = {
            "temperatures": {},
            "humidity": {},
            "motion": {},
            "contact": {},
            "status": "success"
        }
        
        # Process each sensor type
        for device in devices:
            device_id = device.get("id")
            name = device.get("name", device_id)
            zone = device.get("zone", "unknown")
            capabilities = device.get("capabilities", [])
            
            try:
                status = await self.get_device_status(device_id)
                if not status:
                    continue
                    
                # Temperature sensors
                if "measure_temperature" in capabilities and "measure_temperature" in status:
                    temp = status["measure_temperature"]
                    result["temperatures"][name] = {
                        "value": temp,
                        "zone": zone,
                        "unit": "°C"
                    }
                    self._log_message(f"Temperature in {zone} ({name}): {temp}°C")
                
                # Humidity sensors
                if "measure_humidity" in capabilities and "measure_humidity" in status:
                    humidity = status["measure_humidity"]
                    result["humidity"][name] = {
                        "value": humidity,
                        "zone": zone,
                        "unit": "%"
                    }
                    self._log_message(f"Humidity in {zone} ({name}): {humidity}%")
                
                # Motion sensors
                if "alarm_motion" in capabilities and "alarm_motion" in status:
                    motion = status["alarm_motion"]
                    result["motion"][name] = {
                        "value": motion,
                        "zone": zone,
                        "unit": "boolean"
                    }
                    self._log_message(f"Motion in {zone} ({name}): {'detected' if motion else 'no motion'}")
                
                # Contact sensors
                if "alarm_contact" in capabilities and "alarm_contact" in status:
                    contact = status["alarm_contact"]
                    result["contact"][name] = {
                        "value": contact,
                        "zone": zone,
                        "unit": "boolean"
                    }
                    self._log_message(f"Contact in {zone} ({name}): {'open' if contact else 'closed'}")
                    
            except Exception as e:
                self._log_message(f"Error reading sensor {name}: {str(e)}", "error")
                result["status"] = "error"
                
        # Check if we got any readings
        has_readings = any(
            len(result[key]) > 0 
            for key in ["temperatures", "humidity", "motion", "contact"]
        )
        
        if not has_readings:
            self._log_message("No sensor readings available", "warning")
            result["status"] = "error"
            
        return result 