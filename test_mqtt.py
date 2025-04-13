import paho.mqtt.client as mqtt
import yaml
import os
import time

def load_config():
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    # Replace environment variables in config
    for key, value in config.items():
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]
            config[key] = os.getenv(env_var)
            if config[key] is None:
                print(f"Environment variable {env_var} not set")
                raise ValueError(f"Environment variable {env_var} not set")
    
    return config

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    if rc == 0:
        print("Successfully connected to MQTT broker!")
    else:
        print("Failed to connect to MQTT broker")

def on_disconnect(client, userdata, rc):
    print("Disconnected from MQTT broker")

def on_message(client, userdata, msg):
    print(f"📨 Received message on {msg.topic}: {msg.payload.decode()}")

def main():
    config = load_config()
    username = config["mqtt"]["username"]
    password = config["mqtt"]["password"]
    host = config["mqtt"]["host"]
    port = config["mqtt"]["port"]
    
    print(f"Using credentials - Username: {username}, Password: [REDACTED]")
    
    client = mqtt.Client()
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    
    try:
        print("Connecting to MQTT broker...")
        client.connect(host, port, 60)
        client.loop_start()
        
        # Wait for connection
        time.sleep(5)
        
        # Subscribe to test topic
        client.subscribe("test/#")
        
        # Publish test message
        client.publish("test/hello", "Hello from Python!")
        
        # Wait for messages
        time.sleep(5)
        
        client.loop_stop()
        client.disconnect()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main() 