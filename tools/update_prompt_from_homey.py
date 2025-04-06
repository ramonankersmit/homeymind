import requests
import json
import os

# Vul hier je Homey Personal Access Token in:
TOKEN = "XXX"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

HOMEY_API_URL = "https://api.homey.app/v1/devices/"

def fetch_devices():
    response = requests.get(HOMEY_API_URL, headers=HEADERS)
    if response.status_code != 200:
        print(f"Fout bij ophalen devices: {response.status_code}")
        return []

    devices = response.json()
    filtered = []

    for dev in devices:
        name = dev.get("name", "").lower().replace(" ", "_")
        capabilities = dev.get("capabilities", [])
        if any(cap in capabilities for cap in ["onoff", "dim", "volume_set"]):
            filtered.append(name)

    return sorted(set(filtered))


def update_prompt(devices):
    prompt_file = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "prompts", "system_prompt.txt")
    )
    prompt_file = "../prompts/system_prompt.txt"  # pad t.o.v. scriptmap
    try:
        with open(prompt_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        start = None
        for i, line in enumerate(lines):
            if "🧾 Bekende devices" in line:
                start = i
                break

        if start is not None:
            lines = lines[:start+1]
        else:
            lines.append("\n\n🧾 Bekende devices:\n")

        for device in devices:
            lines.append(f"- {device}\n")

        with open(prompt_file, "w", encoding="utf-8") as f:
            f.writelines(lines)

        print(f"✅ Prompt bijgewerkt met {len(devices)} apparaten.")
    except Exception as e:
        print(f"❌ Fout bij updaten prompt: {e}")


if __name__ == "__main__":
    devices = fetch_devices()
    update_prompt(devices)
