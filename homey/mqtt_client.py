import paho.mqtt.publish as publish

def publish_action(intent, config):
    topic = f"{config['mqtt']['topic_prefix']}{intent['device']}"
    message = intent['action'].upper()
    print(f"[MQTT] {topic} = {message}")
    publish.single(
        topic,
        message,
        hostname=config["mqtt"]["host"],
        port=config["mqtt"]["port"]
    )

def publish_tts(message, config):
    topic = "ai/tts"
    print(f"[MQTT] {topic} = {message}")
    publish.single(
        topic,
        message,
        hostname=config["mqtt"]["host"],
        port=config["mqtt"]["port"]
    )

def publish_status(status, config):
    topic = "ai/status"
    print(f"[MQTT] {topic} = {status}")
    publish.single(
        topic,
        status,
        hostname=config["mqtt"]["host"],
        port=config["mqtt"]["port"]
    )

def publish_message(topic, message, config):
    print(f"[MQTT] {topic} = {message}")
    publish.single(
        topic,
        message,
        hostname=config["mqtt"]["host"],
        port=config["mqtt"]["port"]
    )

def publish_tts_agent(message, config):
    publish_message("ai/tts_agent", message, config)

def publish_tts_homey(message, config):
    publish_message("ai/tts_homey", message, config)