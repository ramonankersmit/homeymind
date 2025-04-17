"""
Text-to-Speech Agent for HomeyMind.

This agent handles text-to-speech requests for Homey speakers.
"""

from typing import Dict, Any, Optional
from .base_agent import BaseAgent

class TTSAgent(BaseAgent):
    """Agent for text-to-speech functionality."""
    
    async def process(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process text-to-speech requests.
        
        Args:
            intent (Dict[str, Any]): Intent data containing:
                - text: Text to speak
                - zone (optional): Zone where to play the speech
                - volume (optional): Volume level (0-1)
                
        Returns:
            Dict[str, Any]: Status of the TTS request
        """
        text = intent.get("text")
        if not text:
            self._log_message("No text provided for TTS", "error")
            return {"status": "error", "message": "No text provided"}
            
        # Get speaker configuration
        speakers = self.config.get("speakers", [])
        target_zone = intent.get("zone")
        
        if target_zone:
            # Filter speakers by zone if specified
            speakers = [s for s in speakers if s.get("zone") == target_zone]
            
        if not speakers:
            self._log_message(
                f"No speakers found{f' in zone {target_zone}' if target_zone else ''}", 
                "error"
            )
            return {
                "status": "error", 
                "message": f"No speakers available{f' in zone {target_zone}' if target_zone else ''}"
            }
            
        # Set volume if specified
        volume = intent.get("volume")
        results = []
        
        for speaker in speakers:
            device_id = speaker.get("id")
            name = speaker.get("name", device_id)
            
            try:
                # Set volume if specified
                if volume is not None:
                    await self.execute_device_action(
                        device_id,
                        "volume_set",
                        {"volume": float(volume)}
                    )
                    self._log_message(f"Set volume to {volume} for {name}")
                
                # Send TTS command
                await self.execute_device_action(
                    device_id,
                    "speaker_say",
                    {"text": text}
                )
                
                self._log_message(f"TTS executed on {name}: {text}")
                results.append({
                    "speaker": name,
                    "status": "success"
                })
                
            except Exception as e:
                self._log_message(f"Error executing TTS on {name}: {str(e)}", "error")
                results.append({
                    "speaker": name,
                    "status": "error",
                    "error": str(e)
                })
                
        return {
            "status": "success" if any(r["status"] == "success" for r in results) else "error",
            "results": results
        } 