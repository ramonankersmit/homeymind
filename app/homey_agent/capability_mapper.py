import json
import os

CAPABILITY_CONFIG_PATH = "capabilities.json"

DEFAULT_CAPABILITIES = {
    "licht": {
        "onoff": {
            "settable": True,
            "payloads": {
                "aanzetten": "on",
                "uitzetten": "off"
            }
        },
        "dim": {
            "settable": True,
            "payloads": {}
        }
    },
    "gordijn": {
        "windowcoverings_state": {
            "settable": True,
            "payloads": {
                "openen": "open",
                "dichtdoen": "close"
            }
        }
    },
    "sensor": {
        "measure-temperature": {
            "settable": False
        }
    }
}

def load_capabilities():
    if os.path.exists(CAPABILITY_CONFIG_PATH):
        with open(CAPABILITY_CONFIG_PATH, 'r') as f:
            return json.load(f)
    else:
        return DEFAULT_CAPABILITIES

def save_capabilities(capabilities):
    with open(CAPABILITY_CONFIG_PATH, 'w') as f:
        json.dump(capabilities, f, indent=2)

def check_new_capabilities(discovered_devices, capabilities):
    new_found = {}
    for dev_id, data in discovered_devices.items():
        name = data.get("name", "onbekend")
        for key in data.keys():
            if key not in ["name"]:
                found = False
                for cap_type in capabilities.values():
                    if key in cap_type:
                        found = True
                        break
                if not found:
                    new_found.setdefault(dev_id, []).append(key)
    return new_found

def add_new_capabilities(capabilities, new_caps):
    for device_id, props in new_caps.items():
        for prop in props:
            capabilities.setdefault("onbekend", {})[prop] = {
                "settable": True,
                "payloads": {}
            }
    save_capabilities(capabilities)
