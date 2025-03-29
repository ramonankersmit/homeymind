import json
import re

def parse_intent(response):
    # Zoek eerste JSON-achtig blok uit LLM-respons
    match = re.search(r'\{.*?\}', response, re.DOTALL)
    if not match:
        print("[WARN] Geen JSON-herkenning in respons")
        return None
    try:
        parsed = json.loads(match.group(0))
        if "device" in parsed and "action" in parsed:
            return {
                "device": parsed["device"].strip().lower().replace(" ", "_"),
                "action": parsed["action"].strip().lower()
            }
        else:
            print("[WARN] JSON mist vereiste velden")
            return None
    except json.JSONDecodeError as e:
        print(f"[WARN] Fout bij JSON-decodering: {e}")
        return None