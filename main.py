"""
HomeyMind - A voice-controlled home automation system.

This module implements the main application logic for HomeyMind, including:
- Voice command processing
- Device control through MQTT
- LLM-based intent recognition
- Wake word detection
- Audio transcription

The application follows this workflow:
1. Wait for wake word
2. Listen for command
3. Process command through LLM
4. Execute device control through MQTT
"""

import asyncio
import os
import time
import yaml
from dotenv import load_dotenv
from audio.wake_word_vosk import wait_for_wake_word
from audio.transcriber import transcribe_audio
from homey.mqtt_client import get_client
from utils.intent_parser import parse_intent, validate_intent, Intent, ActionType
from utils.device_list import KNOWN_DEVICES, update_device_list
from utils.device_suggestion import suggest_closest_devices
from llm_manager import LLMManager
from utils.memory import Memory
import logging
from datetime import datetime
from typing import Dict, Any
from audio.recorder import record_audio_v2
from agents import CoordinatorAgent, PlannerAgent, HomeyAgent, LoggerAgent
from homey.mqtt_client import MQTTClient

# Load environment variables from .env file
load_dotenv()

# Maak logs-map aan als die nog niet bestaat
os.makedirs("logs", exist_ok=True)    
# Logging configureren
logging.basicConfig(
    filename="logs/topper.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Add console handler to show logs in terminal
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def log_event(event: str) -> None:
    """
    Log an event to the application log file.
    
    Args:
        event (str): The event message to log.
    """
    logging.info(event)

def load_config() -> dict:
    """
    Load and process the configuration file.
    
    This function:
    1. Loads the YAML configuration file
    2. Replaces environment variables in the config
    3. Validates required environment variables
    
    Returns:
        dict: The processed configuration dictionary.
        
    Raises:
        ValueError: If a required environment variable is not set.
    """
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    def replace_env_vars(obj):
        if isinstance(obj, str):
            if obj.startswith("${") and obj.endswith("}"):
                env_var = obj[2:-1]
                value = os.getenv(env_var)
                if value is None:
                    logging.error(f"Environment variable {env_var} not set")
                    raise ValueError(f"Environment variable {env_var} not set")
                return value
            return obj
        elif isinstance(obj, dict):
            return {k: replace_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [replace_env_vars(item) for item in obj]
        return obj
    
    config = replace_env_vars(config)
    return config

def process_command(command: str, llm_manager: LLMManager) -> Intent:
    """
    Process a voice command through the LLM to extract intent.
    
    Args:
        command (str): The voice command to process.
        llm_manager (LLMManager): The LLM manager instance for processing.
        
    Returns:
        Intent: The parsed intent containing device and action information.
        
    Raises:
        ValueError: If the command cannot be processed or intent is invalid.
    """
    # Process command through LLM
    intent = parse_intent(command, llm_manager)
    
    # Validate intent
    if not validate_intent(intent):
        raise ValueError("Invalid intent")
        
    return intent

def execute_intent(intent: Intent, mqtt_client) -> None:
    """
    Execute a device control intent through MQTT.
    
    Args:
        intent (Intent): The intent to execute.
        mqtt_client: The MQTT client instance.
        
    Raises:
        ValueError: If the device is not found or action cannot be executed.
    """
    # Find device in known devices
    device = next((d for d in KNOWN_DEVICES if d.name.lower() == intent.device.lower()), None)
    if not device:
        raise ValueError(f"Device {intent.device} not found")
        
    # Execute action
    if intent.action == ActionType.TURN_ON:
        device.turn_on(mqtt_client)
    elif intent.action == ActionType.TURN_OFF:
        device.turn_off(mqtt_client)
    else:
        raise ValueError(f"Unsupported action: {intent.action}")

async def process_command(text: str, config: Dict[str, Any], mqtt_client: MQTTClient, memory: Memory) -> None:
    """Process a voice command using the agent system."""
    # Initialize agents
    coordinator = CoordinatorAgent(config, mqtt_client)
    planner = PlannerAgent(config)
    homey = HomeyAgent(config, mqtt_client)
    logger_agent = LoggerAgent(config)
    
    # Create input data
    input_data = {
        "text": text,
        "timestamp": datetime.now().isoformat(),
        "agent": "user"
    }
    
    # Process through coordinator
    result = await coordinator.process(input_data)
    
    # Log the result
    if result:
        await logger_agent.process({
            "type": "action",
            "data": result,
            "timestamp": datetime.now().isoformat(),
            "agent": "coordinator"
        })

async def main():
    """Main function to run the HomeyMind system."""
    try:
        # Load configuration
        config = load_config()
        logger.info("Configuration loaded successfully")
        
        # Initialize MQTT client
        mqtt_client = get_client(config)
        mqtt_client.connect()
        logger.info("MQTT client initialized")
        
        # Initialize memory
        memory = Memory()
        logger.info("Memory system initialized")
        
        # Main loop
        while True:
            try:
                # Wait for wake word
                if not wait_for_wake_word(wake_word=config["audio"]["wake_word"]):
                    continue
                logger.info("Wake word detected")
                mqtt_client.publish_tts_agent("Oké, ik luister")
                mqtt_client.publish_status("Luistert naar opdracht")
                
                # Record and transcribe command
                duration = float(config["audio"]["record_seconds"])  # Convert to float
                audio_data = record_audio_v2(duration)  # Pass as positional argument
                text = transcribe_audio(audio_data)  # Use default parameters
                logger.info(f"Transcribed command: {text}")
                
                # Process command
                await process_command(text, config, mqtt_client, memory)
                
            except KeyboardInterrupt:
                logger.info("Command processing interrupted")
                break
            except Exception as e:
                logger.error(f"Error processing command: {str(e)}", exc_info=True)
                mqtt_client.publish_tts_agent("Sorry, er ging iets mis. Probeer het nog eens.")
                continue
    
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())