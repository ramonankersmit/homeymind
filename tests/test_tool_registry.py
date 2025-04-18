import pytest
from app.agents.tool_registry import Tool, register_tool, get_tool, get_all_tools
from app.agents.schemas import SensorDataInput, SensorDataOutput

def test_tool_registration():
    """Test tool registration and retrieval."""
    # Create a test tool
    def test_func(input_data):
        return {"status": "success", "temperature": 20.0}
    
    tool = Tool(
        name="test_tool",
        func=test_func,
        input_model=SensorDataInput,
        output_model=SensorDataOutput,
        description="Test tool"
    )
    
    # Register tool
    register_tool(tool)
    
    # Test retrieval
    retrieved = get_tool("test_tool")
    assert retrieved.name == "test_tool"
    assert retrieved.description == "Test tool"
    
    # Test get all tools
    all_tools = get_all_tools()
    assert "test_tool" in all_tools
    
    # Test duplicate registration
    with pytest.raises(ValueError):
        register_tool(tool)
    
    # Test non-existent tool
    with pytest.raises(ValueError):
        get_tool("non_existent")

def test_tool_validation():
    """Test tool input/output validation."""
    def test_func(input_data):
        return {"status": "success", "temperature": 20.0}
    
    tool = Tool(
        name="test_tool",
        func=test_func,
        input_model=SensorDataInput,
        output_model=SensorDataOutput,
        description="Test tool"
    )
    
    # Test valid input
    input_data = {"zone": "living_room"}
    validated = tool.validate_input(input_data)
    assert validated.zone == "living_room"
    
    # Test invalid input
    with pytest.raises(Exception):
        tool.validate_input({"invalid": "data"})
    
    # Test valid output
    output_data = {"status": "success", "temperature": 20.0}
    validated = tool.validate_output(output_data)
    assert validated.status == "success"
    assert validated.temperature == 20.0
    
    # Test invalid output
    with pytest.raises(Exception):
        tool.validate_output({"invalid": "data"}) 