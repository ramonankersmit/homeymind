from capability_mapper import load_capabilities, check_new_capabilities, add_new_capabilities
from device_discovery import discover_devices


def run_capability_check():
    print("Start capability check...")
    devices = discover_devices()
    capabilities = load_capabilities()
    new_caps = check_new_capabilities(devices, capabilities)

    if new_caps:
        print("Nieuwe (nog niet gemappte) capabilities gevonden:")
        for device, props in new_caps.items():
            print(f"- {device}: {props}")
        add_new_capabilities(capabilities, new_caps)
        print("Toegevoegd aan capabilities.json onder 'onbekend'.")
    else:
        print("Geen nieuwe capabilities gevonden. Alles is up-to-date.")


if __name__ == "__main__":
    run_capability_check()