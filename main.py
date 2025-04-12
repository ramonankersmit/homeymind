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

def log_event(event):
    logging.info(event)

def load_config():
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    # Replace environment variables in config
    for key, value in config.items():
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]
            config[key] = os.getenv(env_var)
            if config[key] is None:
                logging.error(f"Environment variable {env_var} not set")
                raise ValueError(f"Environment variable {env_var} not set")
    
    return config

# Config laden
config = load_config()

# Init LLM manager
last_mode = recall("llm_mode", "local")
llm = LLMManager(
    mode="local",
    local_model=config["llm"].get("local_model", "mistral"),
    cloud_model=config["llm"].get("cloud_model", "gpt-4o"),
    openai_api_key=config.get("openai_api_key")
)

# Initialize MQTT client
mqtt_client = get_client(config)
mqtt_client.connect()

# Update device list from MQTT
update_device_list(config)

mqtt_client.publish_status("Topper is opgestart")
print("AI-agent klaar. Zeg 'Hey Topper' om te beginnen...")

while True:
    wait_for_wake_word(wake_word=config["audio"]["wake_word"])
    print("* Wake word gedetecteerd!")
    mqtt_client.publish_tts_agent("Oké, ik luister")
    mqtt_client.publish_status("Luistert naar opdracht")

    print("* Luisteren naar opdracht...")
    text = transcribe_audio()
    print(f"* Herkende tekst: {text}")
    log_event(f"Gebruiker: {text}")
    mqtt_client.publish_status(f"Herkenning: {text}")

    with open(config["llm"]["prompt_path"], "r", encoding="utf-8") as f:
        system_prompt = f.read()

    prompt = f"""{system_prompt}

Gebruiker: {text}
Antwoord:"""

    response = llm.ask(prompt)
    print(f"[DEBUG] Ruwe LLM-response: {response}")
    log_event(f"LLM-response: {response}")
    if response.strip() == "[INTERNAL_SWITCH] switch_mode local":
        mqtt_client.publish_tts_agent("Mijn OpenAI-tegoed is op. Ik gebruik nu de lokale AI.")
        mqtt_client.publish_status("Automatisch teruggeschakeld naar lokaal door quota")
        continue

    intent = parse_intent(response)
    if not intent:
        print("[WARN] Geen intent herkend.")
        mqtt_client.publish_tts_agent("Ik heb je verzoek niet goed begrepen.")
        mqtt_client.publish_status("Intent niet herkend")
        continue

    if intent.action_type == ActionType.SWITCH_MODE:
        mode = intent.parameters.get("mode")
        if mode in ["local", "cloud"]:
            llm.set_mode(mode)
            remember("llm_mode", mode)
            msg = "Ik gebruik nu OpenAI." if mode == "cloud" else "Ik gebruik nu de lokale AI."
            mqtt_client.publish_tts_agent(msg)
            mqtt_client.publish_status(f"LLM switched naar {mode}")
        else:
            mqtt_client.publish_tts_agent("Ik weet niet welk AI-model je bedoelt.")
            mqtt_client.publish_status("Ongeldige mode opgegeven")
        continue

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

    log_event(f"Intent: {intent}")
    if mqtt_client.publish_action(intent):
        log_event(f"Actie uitgevoerd: {intent.action} op {intent.device}")
        mqtt_client.publish_tts_agent(f"Oké, ik heb {intent.action} uitgevoerd op {intent.device}.")
        mqtt_client.publish_status(f"{intent.action} uitgevoerd op {intent.device}")
    else:
        mqtt_client.publish_tts_agent("Er is iets misgegaan bij het uitvoeren van de actie.")
        mqtt_client.publish_status("Actie mislukt")