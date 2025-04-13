"""
Test script for AutoGen integration.
"""

import asyncio
import yaml
from homeymind_agents.autogen_manager import AutoGenManager

async def test_autogen():
    """Test the AutoGen integration."""
    # Load configuration
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize AutoGen manager
    autogen_manager = AutoGenManager(config)
    
    # Test intent processing
    test_intent = {
        'text': 'Zet de lichten in de woonkamer aan'
    }
    
    try:
        result = await autogen_manager.process_intent(test_intent)
        print("Test successful!")
        print("Result:", result)
    except Exception as e:
        print("Test failed!")
        print("Error:", str(e))
        raise  # Re-raise the exception for debugging

if __name__ == "__main__":
    asyncio.run(test_autogen()) 