import asyncio
import random
from app.core.circuit_breaker import CircuitBreaker
from app.core.mqtt_client import MQTTClient

async def simulate_mqtt_operation(should_fail: bool = False):
    """Simuleer een MQTT operatie met willekeurige vertraging."""
    await asyncio.sleep(random.uniform(0.1, 0.5))
    if should_fail:
        raise ConnectionError("MQTT connection failed")
    return "success"

async def test_circuit_breaker():
    # Maak een circuit breaker
    breaker = CircuitBreaker(
        name="test_breaker",
        max_delay=2.0,
        max_retries=3,
        open_timeout=5.0,
        success_threshold=2
    )
    
    print("Test 1: Normale operatie")
    try:
        result = await breaker.execute(simulate_mqtt_operation)
        print(f"Resultaat: {result}")
        print(f"State: {breaker.state}")
    except Exception as e:
        print(f"Fout: {e}")
    
    print("\nTest 2: Fout operatie")
    try:
        result = await breaker.execute(lambda: simulate_mqtt_operation(should_fail=True))
        print(f"Resultaat: {result}")
    except Exception as e:
        print(f"Fout: {e}")
        print(f"State: {breaker.state}")
    
    print("\nTest 3: Recovery")
    print("Wachten op half-open state...")
    await asyncio.sleep(6)  # Wacht langer dan open_timeout
    
    try:
        result = await breaker.execute(simulate_mqtt_operation)
        print(f"Resultaat: {result}")
        print(f"State: {breaker.state}")
    except Exception as e:
        print(f"Fout: {e}")

async def test_mqtt_client():
    # MQTT configuratie
    config = {
        "host": "localhost",
        "port": 1883,
        "keepalive": 60
    }
    
    # Maak MQTT client
    client = MQTTClient(config)
    
    print("\nTest MQTT Client")
    try:
        # Test publish
        print("Test publish...")
        await client.publish("test/topic", {"message": "test"})
        print("Publish succesvol")
        
        # Test subscribe
        print("\nTest subscribe...")
        def callback(topic, payload):
            print(f"Bericht ontvangen: {topic} - {payload}")
        
        await client.subscribe("test/topic", callback)
        print("Subscribe succesvol")
        
    except Exception as e:
        print(f"Fout: {e}")
    finally:
        client.disconnect()

if __name__ == "__main__":
    print("Start Circuit Breaker Tests")
    asyncio.run(test_circuit_breaker())
    
    print("\nStart MQTT Client Tests")
    asyncio.run(test_mqtt_client()) 