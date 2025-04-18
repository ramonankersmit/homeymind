# Tool Catalogus

| Tool-naam | Beschrijving | Input-schema | Output-schema | Agent-methode |
|-----------|-------------|--------------|---------------|---------------|
| `get_sensor_data` | Lees sensorwaardes uit een zone | `{ zone: string, device_type?: string }` | `{ status: string, temperature?: number, humidity?: number, motion?: boolean }` | `SensorAgent.process()` |
| `turn_on_device` | Zet één device aan | `{ device_id: string, params?: { brightness?: number } }` | `{ status: string, device_id: string, action: string }` | `DeviceController._execute_action()` |
| `turn_off_device` | Zet één device uit | `{ device_id: string }` | `{ status: string, device_id: string, action: string }` | `DeviceController._execute_action()` |
| `dim_device` | Dim een device | `{ device_id: string, brightness: number }` | `{ status: string, device_id: string, action: string }` | `DeviceController._execute_action()` |
| `speak_text` | Stuur spraak naar speaker(s) | `{ text: string, zone?: string }` | `{ status: string, played_on: string[] }` | `TTSAgent.process()` |
| `get_all_sensors` | Lees alle sensors in een zone | `{ zone: string }` | `{ status: string, sensors: { type: string, value: any }[] }` | `SensorAgent.process_sensor_data()` |
| `get_device_status` | Vraag status van een device | `{ device_id: string }` | `{ status: string, device_id: string, state: any }` | `BaseAgent.get_device_status()` | 