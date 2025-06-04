```mermaid
graph TD
    subgraph frontend["Frontend Interface"]
        ui["React UI\nReal-time chat"]
        sse_client["SSE Client"]
    end

    subgraph cli["CLI Interface"]
        wake_word["Wake Word Detector"]
        recorder["Audio Recorder"]
        stt["Speech-to-Text"]
    end

    subgraph backend["Backend Server"]
        api["FastAPI"]
        autogen_mgr["AutoGen Manager"]
    end

    subgraph agents["Agent System"]
        sensor_agent["SensorAgent"]
        intent_parser["IntentParser"]
        homey_assistant["HomeyAssistant"]
        tts_agent["TTSAgent"]
        light_agent["LightAgent"]
        device_ctrl["DeviceController"]
    end

    subgraph homey["Homey Integratie"]
        homey_ctrl["Homey Controller"]
        homey_devices["Homey Devices"]
        tts_service["Text-to-Speech"]
    end

    ui -->|"HTTP POST /chat"| api
    ui -->|"SSE /chat"| sse_client
    sse_client --> api

    wake_word --> recorder
    recorder --> stt
    stt --> autogen_mgr

    api --> autogen_mgr
    autogen_mgr --> intent_parser
    autogen_mgr --> sensor_agent
    autogen_mgr --> homey_assistant
    autogen_mgr --> tts_agent
    autogen_mgr --> light_agent
    autogen_mgr --> device_ctrl

    device_ctrl --> homey_ctrl
    homey_ctrl -->|MQTT| homey_devices
    homey_ctrl -->|TTS| tts_service

    intent_parser --> autogen_mgr
    sensor_agent --> autogen_mgr
    homey_assistant --> autogen_mgr
    tts_agent --> autogen_mgr
    light_agent --> autogen_mgr
    device_ctrl --> autogen_mgr
    autogen_mgr --> api
    api --> sse_client
    sse_client --> ui
```
