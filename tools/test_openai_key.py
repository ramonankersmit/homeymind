import yaml
import openai

# Config laden
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

api_key = config.get("openai_api_key")

if not api_key:
    print("❌ Geen openai_api_key gevonden in config.yaml.")
    exit(1)

openai.api_key = api_key

try:
    models = openai.models.list()
    print("✅ API-sleutel werkt. Modellen beschikbaar:")
    for m in models.data:
        print("-", m.id)
except Exception as e:
    print("❌ Fout bij ophalen modellen:")
    print(e)