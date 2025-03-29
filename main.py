import os
import time
import yaml
from audio.wake_word_vosk import wait_for_wake_word
from audio.transcriber import transcribe_audio
from homey.mqtt_client import (
    publish_action,
    publish_status,
    publish_tts_agent,
    publish_tts_homey,
)
from utils.intent_parser import parse_intent
from utils.device_list import KNOWN_DEVICES
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

# Config laden
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Init LLM manager
last_mode = recall("llm_mode", "local")
llm = LLMManager(
    mode="local",
    local_model=config["llm"].get("local_model", "mistral"),
    cloud_model=config["llm"].get("cloud_model", "gpt-4o"),
    openai_api_key=config.get("openai_api_key")
)

publish_status("Topper is opgestart", config)
print("AI-agent klaar. Zeg 'Hey Topper' om te beginnen...")

while True:
    wait_for_wake_word(wake_word=config["audio"]["wake_word"])
    print("* Wake word gedetecteerd!")
    publish_tts_agent("Oké, ik luister", config)
    publish_status("Luistert naar opdracht", config)

    print("* Luisteren naar opdracht...")
    text = transcribe_audio()
    print(f"* Herkende tekst: {text}")
    log_event(f"Gebruiker: {text}")
    publish_status(f"Herkenning: {text}", config)

    with open(config["llm"]["prompt_path"], "r", encoding="utf-8") as f:
        system_prompt = f.read()

    prompt = f"""{system_prompt}

Gebruiker: {text}
Antwoord:"""

    response = llm.ask(prompt)
    print(f"[DEBUG] Ruwe LLM-response: {response}")
    log_event(f"LLM-response: {response}")
    if response.strip() == "[INTERNAL_SWITCH] switch_mode local":
        publish_tts_agent("Mijn OpenAI-tegoed is op. Ik gebruik nu de lokale AI.", config)
        publish_status("Automatisch teruggeschakeld naar lokaal door quota", config)
        continue

    intent = parse_intent(response)
    if not intent:
        print("[WARN] Geen intent herkend.")
        publish_tts_agent("Ik heb je verzoek niet goed begrepen.", config)
        publish_status("Intent niet herkend", config)
        continue

    if intent.get("action") == "switch_mode":
        mode = intent.get("mode")
        if mode in ["local", "cloud"]:
            llm.set_mode(mode)
            remember("llm_mode", mode)
            msg = "Ik gebruik nu OpenAI." if mode == "cloud" else "Ik gebruik nu de lokale AI."
            publish_tts_agent(msg, config)
            publish_status(f"LLM switched naar {mode}", config)
        else:
            publish_tts_agent("Ik weet niet welk AI-model je bedoelt.", config)
            publish_status("Ongeldige mode opgegeven", config)
        continue

    if "device" not in intent:
        print("[WARN] Geen geldig apparaat herkend.")
        publish_tts_agent("Ik heb niet goed verstaan welk apparaat je bedoelt.", config)
        publish_status("Geen geldig apparaat", config)
        continue

    if intent["device"] not in KNOWN_DEVICES:
        print(f"[WARN] '{intent['device']}' is geen bekend apparaat.")
        suggestions = suggest_closest_devices(intent["device"], KNOWN_DEVICES)
        if not suggestions:
            publish_tts_agent(f"{intent['device']} is geen bekend apparaat.", config)
            publish_status(f"Onbekend apparaat: {intent['device']}", config)
            continue

        publish_tts_agent(f"'{intent['device']}' is geen bekend apparaat.", config)
        for i, s in enumerate(suggestions, 1):
            publish_tts_agent(f"Optie {i}: {s}", config)
        publish_tts_agent("Zeg nul om te annuleren.", config)
        publish_status("Wacht op apparaatkeuze", config)

        print("* Luisteren naar keuze...")
        choice_text = transcribe_audio()
        print(f"* Keuze herkend: {choice_text}")
        publish_status(f"Keuze: {choice_text}", config)

        mapping = {
            "nul": 0, "één": 1, "een": 1, "twee": 2, "drie": 3,
            "0": 0, "1": 1, "2": 2, "3": 3
        }
        keuze = mapping.get(choice_text.strip().lower(), -1)

        if keuze == 0:
            publish_tts_agent("Actie geannuleerd.", config)
            publish_status("Gebruiker annuleerde keuze", config)
            continue
        elif 1 <= keuze <= len(suggestions):
            intent["device"] = suggestions[keuze - 1]
            publish_tts_agent(f"Ik gebruik nu {intent['device']}.", config)
        else:
            publish_tts_agent("Ik heb geen geldige keuze gehoord.", config)
            publish_status("Ongeldige keuze", config)
            continue

    log_event(f"Intent: {intent}")
    publish_action(intent, config)
    log_event(f"Actie uitgevoerd: {intent['action']} op {intent['device']}")
    publish_tts_agent(f"Oké, ik heb {intent['action']} uitgevoerd op {intent['device']}.", config)
    publish_status(f"{intent['action']} uitgevoerd op {intent['device']}", config)