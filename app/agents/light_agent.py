"""
Light Control Agent for HomeyMind.

This agent handles light control requests for Homey devices.
"""

from typing import Dict, Any, Optional, List
from .base_agent import BaseAgent

class LightAgent(BaseAgent):
    """Agent for controlling lights."""
    
    async def process(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process light control requests.
        
        Args:
            intent (Dict[str, Any]): Intent data containing:
                - action: The action to perform (on/off/dim/color)
                - zone (optional): Zone to control lights in
                - brightness (optional): Brightness level (0-1)
                - color (optional): Color in hex format (#RRGGBB)
                - temperature (optional): Color temperature in Kelvin
                
        Returns:
            Dict[str, Any]: Status of the light control request
        """
        action = intent.get("action", "").lower()
        if not action:
            self._log_message("No action specified for lights", "error")
            return {"status": "error", "message": "No action specified"}
            
        # Get light configuration
        lights = self.config.get("lights", [])
        target_zone = intent.get("zone")
        
        if target_zone:
            # Filter lights by zone if specified
            lights = [l for l in lights if l.get("zone") == target_zone]
            
        if not lights:
            self._log_message(
                f"No lights found{f' in zone {target_zone}' if target_zone else ''}", 
                "error"
            )
            return {
                "status": "error", 
                "message": f"No lights available{f' in zone {target_zone}' if target_zone else ''}"
            }
            
        results = []
        
        for light in lights:
            device_id = light.get("id")
            name = light.get("name", device_id)
            capabilities = light.get("capabilities", [])
            
            try:
                if action in ["on", "off"]:
                    if "onoff" not in capabilities:
                        raise ValueError("Light does not support on/off control")
                    
                    await self.execute_device_action(
                        device_id,
                        "onoff",
                        {"on": action == "on"}
                    )
                    
                elif action == "dim":
                    if "dim" not in capabilities:
                        raise ValueError("Light does not support dimming")
                        
                    brightness = float(intent.get("brightness", 1.0))
                    if not 0 <= brightness <= 1:
                        raise ValueError("Brightness must be between 0 and 1")
                        
                    await self.execute_device_action(
                        device_id,
                        "dim",
                        {"brightness": brightness}
                    )
                    
                elif action == "color":
                    # Handle both RGB color and temperature
                    color = intent.get("color")
                    temperature = intent.get("temperature")
                    
                    if color and "light_hue" in capabilities:
                        # Convert hex color to HSV
                        rgb = tuple(int(color.lstrip("#")[i:i+2], 16)/255 for i in (0, 2, 4))
                        max_rgb = max(rgb)
                        min_rgb = min(rgb)
                        
                        if max_rgb == min_rgb:
                            hue = 0
                        elif max_rgb == rgb[0]:
                            hue = 60 * ((rgb[1] - rgb[2]) / (max_rgb - min_rgb))
                        elif max_rgb == rgb[1]:
                            hue = 60 * (2 + (rgb[2] - rgb[0]) / (max_rgb - min_rgb))
                        else:
                            hue = 60 * (4 + (rgb[0] - rgb[1]) / (max_rgb - min_rgb))
                            
                        if hue < 0:
                            hue += 360
                            
                        saturation = 0 if max_rgb == 0 else (max_rgb - min_rgb) / max_rgb
                        value = max_rgb
                        
                        await self.execute_device_action(
                            device_id,
                            "light_hue",
                            {"hue": hue / 360}  # Homey expects 0-1
                        )
                        
                        if "light_saturation" in capabilities:
                            await self.execute_device_action(
                                device_id,
                                "light_saturation",
                                {"saturation": saturation}
                            )
                            
                    if temperature and "light_temperature" in capabilities:
                        # Convert temperature to 0-1 range (typically 2200K-6500K)
                        temp_min = 2200
                        temp_max = 6500
                        norm_temp = (float(temperature) - temp_min) / (temp_max - temp_min)
                        norm_temp = max(0, min(1, norm_temp))
                        
                        await self.execute_device_action(
                            device_id,
                            "light_temperature",
                            {"temperature": norm_temp}
                        )
                        
                else:
                    raise ValueError(f"Unknown action: {action}")
                    
                self._log_message(f"Light control executed on {name}: {action}")
                results.append({
                    "light": name,
                    "status": "success"
                })
                
            except Exception as e:
                self._log_message(f"Error controlling light {name}: {str(e)}", "error")
                results.append({
                    "light": name,
                    "status": "error",
                    "error": str(e)
                })
                
        return {
            "status": "success" if any(r["status"] == "success" for r in results) else "error",
            "results": results
        } 