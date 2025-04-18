import paho.mqtt.client as mqtt
import json
from typing import Dict, Any, Optional, Callable
import asyncio
from app.core.circuit_breaker import CircuitBreaker
from app.core.observability import get_logger, log_error

class MQTTClient:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.logger = get_logger("mqtt_client")
        
        # Initialize circuit breakers
        self.publish_breaker = CircuitBreaker(
            "mqtt_publish",
            max_delay=2.0,
            max_retries=3,
            exceptions=(ConnectionError, TimeoutError)
        )
        self.subscribe_breaker = CircuitBreaker(
            "mqtt_subscribe",
            max_delay=2.0,
            max_retries=3,
            exceptions=(ConnectionError, TimeoutError)
        )
        
        # Connect to broker
        self.client.connect(
            config["host"],
            config["port"],
            config["keepalive"]
        )
        self.client.loop_start()
    
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.logger.info("mqtt_connected")
        else:
            log_error(
                self.logger,
                Exception(f"MQTT connection failed with code {rc}"),
                {"rc": rc}
            )
    
    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload)
            self.logger.info(
                "mqtt_message_received",
                topic=msg.topic,
                payload=payload
            )
        except json.JSONDecodeError as e:
            log_error(
                self.logger,
                e,
                {"topic": msg.topic, "payload": msg.payload}
            )
    
    async def publish(self, topic: str, payload: Dict[str, Any]) -> None:
        """Publish a message with circuit breaker protection."""
        try:
            await self.publish_breaker.execute(
                self._publish,
                topic,
                json.dumps(payload)
            )
        except Exception as e:
            log_error(
                self.logger,
                e,
                {"topic": topic, "payload": payload}
            )
            raise
    
    def _publish(self, topic: str, payload: str) -> None:
        """Internal publish method."""
        self.client.publish(topic, payload)
    
    async def subscribe(self, topic: str, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Subscribe to a topic with circuit breaker protection."""
        try:
            await self.subscribe_breaker.execute(
                self._subscribe,
                topic,
                callback
            )
        except Exception as e:
            log_error(
                self.logger,
                e,
                {"topic": topic}
            )
            raise
    
    def _subscribe(self, topic: str, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Internal subscribe method."""
        self.client.subscribe(topic)
        self.client.message_callback_add(topic, lambda c, u, m: callback(m.topic, json.loads(m.payload)))
    
    def disconnect(self) -> None:
        """Disconnect from the broker."""
        self.client.loop_stop()
        self.client.disconnect() 