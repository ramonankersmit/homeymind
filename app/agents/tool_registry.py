from typing import Callable, Dict, Type
from pydantic import BaseModel
from .schemas import (
    SensorDataInput, SensorDataOutput,
    DeviceActionInput, DeviceActionOutput,
    DimDeviceInput, TTSInput, TTSOutput,
    AllSensorsInput, AllSensorsOutput,
    DeviceStatusInput, DeviceStatusOutput
)

class Tool:
    def __init__(
        self,
        name: str,
        func: Callable,
        input_model: Type[BaseModel],
        output_model: Type[BaseModel],
        description: str
    ):
        self.name = name
        self.func = func
        self.input_model = input_model
        self.output_model = output_model
        self.description = description

    def validate_input(self, input_data: Dict) -> BaseModel:
        return self.input_model(**input_data)

    def validate_output(self, output_data: Dict) -> BaseModel:
        return self.output_model(**output_data)

registry: Dict[str, Tool] = {}

def register_tool(tool: Tool):
    if tool.name in registry:
        raise ValueError(f"Tool {tool.name} is already registered")
    registry[tool.name] = tool

def get_tool(name: str) -> Tool:
    if name not in registry:
        raise ValueError(f"Tool {name} not found")
    return registry[name]

def get_all_tools() -> Dict[str, Tool]:
    return registry.copy() 