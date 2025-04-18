import pytest
import json
import tempfile
from openai import OpenAI
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def valid_llm_config():
    """
    Matches autogen's LLMConfig schema
    """
    return {
        "config_list": [
            {
                "model": "gpt-4",
                "api_key": "dummy-key",
                "base_url": "https://api.openai.com/v1"
            }
        ],
        "temperature": 0.7
    }

@pytest.fixture
def mock_device_config():
    """Create a temporary device configuration file."""
    config = {
        "zones": {
            "woonkamer": [
                {
                    "id": "light_1",
                    "name": "Living Room Light",
                    "type": "light",
                    "capabilities": ["onoff", "dim"]
                }
            ],
            "keuken": [
                {
                    "id": "thermostat_1",
                    "name": "Kitchen Thermostat",
                    "type": "thermostat",
                    "capabilities": ["target_temperature"]
                }
            ]
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        json.dump(config, f)
        return f.name

@pytest.fixture(autouse=True)
def stub_openai(monkeypatch):
    class DummyClient:
        def __init__(self, *args, **kwargs):
            self.base_url = "https://api.openai.com/v1"
            self.chat = type("DummyChat", (), {
                "completions": type("DummyCompletions", (), {
                    "create": lambda *args, **kwargs: MagicMock(choices=[MagicMock(message=MagicMock(content="{}"))]),
                })()
            })()

    def mock_init(self, **kwargs):
        self.chat = DummyClient().chat
        return None

    monkeypatch.setattr(OpenAI, "__init__", mock_init)