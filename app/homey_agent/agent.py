from utils.intent_parser import parse_intent as parse_command
from homey.mqtt_client import publish_action as send_to_homey, publish_message as action_to_mqtt


def run_agent():
    print("Welkom bij je Homey AI-agent. Typ een commando, of 'stop' om te stoppen.")
    while True:
        user_input = input(">> ")
        if user_input.lower() in ["stop", "exit", "quit"]:
            print("Agent gestopt.")
            break

        actie = parse_command(user_input)
        if not actie:
            print("Kon het commando niet interpreteren.")
            continue

        topic, payload = action_to_mqtt(actie)
        if topic and payload:
            send_to_homey(topic, payload)
        else:
            print("Actie kon niet worden uitgevoerd. Controleer je apparaten en locatie.")


if __name__ == "__main__":
    run_agent()