"""
Text-to-Speech Agent for HomeyMind.

This agent handles text-to-speech conversion and audio playback across multiple speakers.
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent

class TTSAgent(BaseAgent):
    """Agent responsible for text-to-speech conversion and audio playback."""
    
    def __init__(self, config: Dict[str, Any], mqtt_client=None, tts_config: Dict[str, Any] = None):
        """Initialize the TTS agent.
        
        Args:
            config: General configuration dictionary
            mqtt_client: Optional MQTT client for communication
            tts_config: TTS-specific configuration dictionary
        """
        super().__init__(config, mqtt_client)
        
        # Merge TTS config with general config
        self.config = {**config, **(tts_config or {})}
        self.speakers = self.config.get("speakers", [])
        self.default_volume = self.config.get("default_volume", 50)
        self.default_zone = self.config.get("default_zone", "all")
        
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process text-to-speech request.
        
        Args:
            request: Dictionary containing:
                - text: Text to convert to speech
                - zone: Optional target zone for playback
                - volume: Optional volume level (0-100)
            
        Returns:
            Dict containing:
                - status: "success" or "error"
                - message: Success/error message
        """
        text = request.get("text", "")
        zone = request.get("zone", self.default_zone)
        volume = request.get("volume", self.default_volume)
        
        if not text:
            return {
                "status": "error",
                "message": "No text provided for TTS conversion"
            }
            
        # Get speakers for the specified zone
        target_speakers = self._get_speakers_for_zone(zone)
        if not target_speakers:
            return {
                "status": "error",
                "message": f"No speakers available in zone: {zone}"
            }
            
        try:
            # Convert text to speech
            audio_data = await self._text_to_speech(text)
            
            # Play on each speaker
            for speaker in target_speakers:
                try:
                    # Publish audio data to speaker
                    await self.mqtt_client.publish(
                        f"speakers/{speaker['id']}/play",
                        {
                            "audio_data": audio_data,
                            "volume": volume
                        }
                    )
                except Exception as e:
                    return {
                        "status": "error",
                        "message": f"Failed to play audio on speaker {speaker['id']}: {str(e)}"
                    }
                    
            return {
                "status": "success",
                "message": f"TTS enqueued for zone {zone}"
            }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error during TTS processing: {str(e)}"
            }
            
    async def _text_to_speech(self, text: str) -> bytes:
        """Convert text to speech audio data.
        
        Args:
            text: Text to convert
            
        Returns:
            Audio data as bytes
            
        Raises:
            Exception: If conversion fails
        """
        # TODO: Implement actual TTS conversion
        # For now, simulate audio data
        return b"simulated_audio_data"
            
    def _get_speakers_for_zone(self, zone: str) -> List[Dict[str, Any]]:
        """Get speakers for the specified zone.
        
        Args:
            zone: Target zone name
            
        Returns:
            List of speakers in the zone
        """
        if zone == "all":
            return self.speakers
            
        return [
            speaker
            for speaker in self.speakers
            if speaker.get("zone") == zone
        ] 