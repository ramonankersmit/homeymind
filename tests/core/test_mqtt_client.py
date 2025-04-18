import pytest
import asyncio
from unittest.mock import Mock, patch
from app.core.mqtt_client import MQTTClient

@pytest.fixture
def mqtt_config():
    return {
        "host": "localhost",
        "port": 1883,
        "keepalive": 60
    }

@pytest.fixture
def mock_mqtt_client():
    with patch("paho.mqtt.client.Client") as mock:
        yield mock

@pytest.mark.asyncio
async def test_mqtt_client_publish_success(mqtt_config, mock_mqtt_client):
    client = MQTTClient(mqtt_config)
    topic = "test/topic"
    payload = {"message": "test"}
    
    await client.publish(topic, payload)
    
    mock_mqtt_client.return_value.publish.assert_called_once_with(
        topic,
        '{"message": "test"}'
    )

@pytest.mark.asyncio
async def test_mqtt_client_publish_failure(mqtt_config, mock_mqtt_client):
    client = MQTTClient(mqtt_config)
    topic = "test/topic"
    payload = {"message": "test"}
    
    mock_mqtt_client.return_value.publish.side_effect = Exception("Publish failed")
    
    with pytest.raises(Exception):
        await client.publish(topic, payload)
    
    assert client.publish_breaker.state == "open"

@pytest.mark.asyncio
async def test_mqtt_client_subscribe_success(mqtt_config, mock_mqtt_client):
    client = MQTTClient(mqtt_config)
    topic = "test/topic"
    callback = Mock()
    
    await client.subscribe(topic, callback)
    
    mock_mqtt_client.return_value.subscribe.assert_called_once_with(topic)
    assert len(mock_mqtt_client.return_value.message_callback_add.call_args_list) == 1

@pytest.mark.asyncio
async def test_mqtt_client_subscribe_failure(mqtt_config, mock_mqtt_client):
    client = MQTTClient(mqtt_config)
    topic = "test/topic"
    callback = Mock()
    
    mock_mqtt_client.return_value.subscribe.side_effect = Exception("Subscribe failed")
    
    with pytest.raises(Exception):
        await client.subscribe(topic, callback)
    
    assert client.subscribe_breaker.state == "open"

@pytest.mark.asyncio
async def test_mqtt_client_recovery(mqtt_config, mock_mqtt_client):
    client = MQTTClient(mqtt_config)
    topic = "test/topic"
    payload = {"message": "test"}
    
    # Force open state
    mock_mqtt_client.return_value.publish.side_effect = Exception("Publish failed")
    with pytest.raises(Exception):
        await client.publish(topic, payload)
    
    assert client.publish_breaker.state == "open"
    
    # Wait for timeout
    await asyncio.sleep(0.2)
    
    # Try again with success
    mock_mqtt_client.return_value.publish.side_effect = None
    await client.publish(topic, payload)
    
    assert client.publish_breaker.state == "closed" 