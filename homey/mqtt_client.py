import paho.mqtt.client as mqtt
from typing import Dict, Optional, Union
from utils.intent_parser import Intent, ActionType
import json
import time

class MQTTClient:
    def __init__(self, config: Dict):
        self.config = config
        self.client = None
        self.connected = False
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the MQTT client with callbacks."""
        self.client = mqtt.Client()
        self.client.username_pw_set(
            self.config["mqtt"]["username"],
            self.config["mqtt"]["password"]
        )
        
        # Set up callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker."""
        if rc == 0:
            print("[MQTT] Connected to broker")
            self.connected = True
        else:
            print(f"[MQTT] Connection failed with code {rc}")
            self.connected = False

    def _on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects from the broker."""
        print("[MQTT] Disconnected from broker")
        self.connected = False

    def _on_message(self, client, userdata, msg):
        """Callback for when a message is received."""
        print(f"[MQTT] Received message on {msg.topic}: {msg.payload.decode()}")

    def connect(self):
        """Connect to the MQTT broker."""
        if not self.connected:
            try:
                self.client.connect(
                    self.config["mqtt"]["host"],
                    self.config["mqtt"]["port"],
                    60
                )
                self.client.loop_start()
                # Wait for connection
                for _ in range(5):
                    if self.connected:
                        break
                    time.sleep(0.1)
            except Exception as e:
                print(f"[MQTT Error] Connection failed: {str(e)}")
                self.connected = False

    def disconnect(self):
        """Disconnect from the MQTT broker."""
        if self.connected:
            try:
                self.client.loop_stop()
                self.client.disconnect()
                self.connected = False
            except Exception as e:
                print(f"[MQTT Error] Disconnection failed: {str(e)}")

    def publish_action(self, intent: Intent):
        """Publish an action to the MQTT broker."""
        if not self.connected:
            self.connect()
            if not self.connected:
                return False

        try:
            topic = f"{self.config['mqtt']['topic_prefix']}{intent.device}"
            
            # Handle different action types
            if intent.action_type == ActionType.ONOFF:
                message = "ON" if intent.value else "OFF"
            elif intent.action_type == ActionType.DIM:
                # Convert dim value to percentage (0-100)
                dim_value = int(intent.value * 100) if intent.value is not None else 0
                message = str(dim_value)
            elif intent.action_type == ActionType.SWITCH_MODE:
                message = intent.action.upper()
            else:
                print(f"[MQTT] Unknown action type: {intent.action_type}")
                return False

            print(f"[MQTT] {topic} = {message}")
            self.client.publish(topic, message)
            return True
        except Exception as e:
            print(f"[MQTT Error] {str(e)}")
            return False

    def publish_tts(self, message: str):
        """Publish a TTS message."""
        return self._publish_message("ai/tts", message)

    def publish_status(self, status: str):
        """Publish a status message."""
        return self._publish_message("ai/status", status)

    def publish_tts_agent(self, message: str):
        """Publish a TTS message for the agent."""
        return self._publish_message("ai/tts_agent", message)

    def publish_tts_homey(self, message: str):
        """Publish a TTS message for Homey."""
        return self._publish_message("ai/tts_homey", message)

    def _publish_message(self, topic: str, message: str) -> bool:
        """Internal method to publish a message."""
        if not self.connected:
            self.connect()
            if not self.connected:
                return False

        try:
            print(f"[MQTT] {topic} = {message}")
            self.client.publish(topic, message)
            return True
        except Exception as e:
            print(f"[MQTT Error] {str(e)}")
            return False

# Global instance for backward compatibility
_client_instance = None

def get_client(config: Dict) -> MQTTClient:
    """Get or create a MQTT client instance."""
    global _client_instance
    if _client_instance is None:
        _client_instance = MQTTClient(config)
    return _client_instance

# Backward compatibility functions
def publish_action(intent: Dict, config: Dict):
    """Legacy function for backward compatibility."""
    client = get_client(config)
    parsed_intent = Intent(
        device=intent["device"],
        action=intent["action"],
        action_type=ActionType.ONOFF if intent["action"].lower() in ["on", "off"] else ActionType.UNKNOWN,
        value=intent["action"].lower() == "on"
    )
    return client.publish_action(parsed_intent)

def publish_tts(message: str, config: Dict):
    """Legacy function for backward compatibility."""
    return get_client(config).publish_tts(message)

def publish_status(status: str, config: Dict):
    """Legacy function for backward compatibility."""
    return get_client(config).publish_status(status)

def publish_message(topic: str, message: str, config: Dict):
    """Legacy function for backward compatibility."""
    return get_client(config)._publish_message(topic, message)

def publish_tts_agent(message: str, config: Dict):
    """Legacy function for backward compatibility."""
    return get_client(config).publish_tts_agent(message)

def publish_tts_homey(message: str, config: Dict):
    """Legacy function for backward compatibility."""
    return get_client(config).publish_tts_homey(message)