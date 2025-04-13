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

import os
import time
import yaml
from audio.wake_word_vosk import wait_for_wake_word
from audio.transcriber import transcribe_audio
from homey.mqtt_client import get_client
from utils.intent_parser import parse_intent, validate_intent, Intent, ActionType
from utils.device_list import KNOWN_DEVICES, update_device_list
from utils.device_suggestion import suggest_closest_devices
from llm_manager import LLMManager
from memory import remember, recall
import logging

# Maak logs-map aan als die nog niet bestaat
os.makedirs("logs", exist_ok=True)    
# Logging configureren
logging.basicConfig(
    filename="logs/topper.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

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

def main():
    """
    Main application entry point.
    
    This function:
    1. Loads configuration
    2. Initializes MQTT client
    3. Sets up LLM manager
    4. Enters main command processing loop
    """
    try:
        config = load_config()
        log_event("Starting HomeyMind...")

        # Initialize components
        mqtt_client = get_client(config)
        mqtt_client.connect()
        
        # Initialize LLM manager
        llm_manager = LLMManager(config)
        wake_word_detector = wait_for_wake_word
        transcriber = transcribe_audio
        recorder = None  # Assuming Recorder is not used in the original code
        device_list = KNOWN_DEVICES
        device_suggester = suggest_closest_devices
        intent_parser = parse_intent

        # Update device list from MQTT
        update_device_list(config)
        
        log_event("HomeyMind started")
        mqtt_client.publish_status(f"{config['audio']['wake_word'].capitalize()} is opgestart")
        print(f"AI-agent klaar. Zeg 'Hey {config['audio']['wake_word'].capitalize()}' om te beginnen...")
        
        while True:
            try:
                # Wait for wake word
                if not wait_for_wake_word(wake_word=config["audio"]["wake_word"]):
                    continue
                print("* Wake word gedetecteerd!")
                mqtt_client.publish_tts_agent("Oké, ik luister")
                mqtt_client.publish_status("Luistert naar opdracht")
                
                # Listen for command
                print("* Luisteren naar opdracht...")
                command = transcribe_audio()
                if not command:
                    continue
                    
                print(f"* Herkende tekst: {command}")
                log_event(f"Gebruiker: {command}")
                mqtt_client.publish_status(f"Herkenning: {command}")
                
                # Process command through LLM
                with open(config["llm"]["prompt_path"], "r", encoding="utf-8") as f:
                    system_prompt = f.read()

                prompt = f"""{system_prompt}

Gebruiker: {command}
Antwoord:"""

                response = llm_manager.ask(prompt)
                log_event(f"LLM-response: {response}")
                
                # Check for mode switch
                if response.strip() == "[INTERNAL_SWITCH] switch_mode local":
                    mqtt_client.publish_tts_agent("Mijn OpenAI-tegoed is op. Ik gebruik nu de lokale AI.")
                    mqtt_client.publish_status("Automatisch teruggeschakeld naar lokaal door quota")
                    continue
                
                # Parse and validate intent
                intent = parse_intent(response)
                if not intent:
                    print("[WARN] Geen intent herkend.")
                    mqtt_client.publish_tts_agent("Ik heb je verzoek niet goed begrepen.")
                    mqtt_client.publish_status("Intent niet herkend")
                    continue
                
                # Handle mode switch intent
                if intent.action_type == ActionType.SWITCH_MODE:
                    mode = intent.parameters.get("mode")
                    if mode in ["local", "cloud"]:
                        llm_manager.set_mode(mode)
                        remember("llm_mode", mode)
                        msg = "Ik gebruik nu OpenAI." if mode == "cloud" else "Ik gebruik nu de lokale AI."
                        mqtt_client.publish_tts_agent(msg)
                        mqtt_client.publish_status(f"LLM switched naar {mode}")
                    else:
                        mqtt_client.publish_tts_agent("Ik weet niet welk AI-model je bedoelt.")
                        mqtt_client.publish_status("Ongeldige mode opgegeven")
                    continue
                
                # Validate device
                if not validate_intent(intent, KNOWN_DEVICES):
                    print(f"[WARN] '{intent.device}' is geen bekend apparaat.")
                    suggestions = suggest_closest_devices(intent.device, KNOWN_DEVICES)
                    if not suggestions:
                        mqtt_client.publish_tts_agent(f"{intent.device} is geen bekend apparaat.")
                        mqtt_client.publish_status(f"Onbekend apparaat: {intent.device}")
                        continue

                    mqtt_client.publish_tts_agent(f"'{intent.device}' is geen bekend apparaat.")
                    for i, s in enumerate(suggestions, 1):
                        mqtt_client.publish_tts_agent(f"Optie {i}: {s}")
                    mqtt_client.publish_tts_agent("Zeg nul om te annuleren.")
                    mqtt_client.publish_status("Wacht op apparaatkeuze")

                    print("* Luisteren naar keuze...")
                    choice_text = transcribe_audio()
                    print(f"* Keuze herkend: {choice_text}")
                    mqtt_client.publish_status(f"Keuze: {choice_text}")

                    mapping = {
                        "nul": 0, "één": 1, "een": 1, "twee": 2, "drie": 3,
                        "0": 0, "1": 1, "2": 2, "3": 3
                    }
                    keuze = mapping.get(choice_text.strip().lower(), -1)

                    if keuze == 0:
                        mqtt_client.publish_tts_agent("Actie geannuleerd.")
                        mqtt_client.publish_status("Gebruiker annuleerde keuze")
                        continue
                    elif 1 <= keuze <= len(suggestions):
                        intent.device = suggestions[keuze - 1]
                        mqtt_client.publish_tts_agent(f"Ik gebruik nu {intent.device}.")
                    else:
                        mqtt_client.publish_tts_agent("Ik heb geen geldige keuze gehoord.")
                        mqtt_client.publish_status("Ongeldige keuze")
                        continue
                
                # Execute intent
                log_event(f"Intent: {intent}")
                if mqtt_client.publish_action(intent):
                    log_event(f"Actie uitgevoerd: {intent.action} op {intent.device}")
                    mqtt_client.publish_tts_agent(f"Oké, ik heb {intent.action} uitgevoerd op {intent.device}.")
                    mqtt_client.publish_status(f"{intent.action} uitgevoerd op {intent.device}")
                else:
                    mqtt_client.publish_tts_agent("Er is iets misgegaan bij het uitvoeren van de actie.")
                    mqtt_client.publish_status("Actie mislukt")
                
            except Exception as e:
                log_event(f"Error processing command: {str(e)}")
                mqtt_client.publish_tts_agent("Er is iets misgegaan bij het verwerken van je opdracht.")
                mqtt_client.publish_status(f"Fout: {str(e)}")
                continue
                
    except Exception as e:
        log_event(f"Fatal error: {str(e)}")
        raise

if __name__ == "__main__":
    main()