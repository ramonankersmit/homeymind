import json
import os

MEMORY_FILE = "memory.json"

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_memory(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def remember(key, value):
    mem = load_memory()
    mem[key] = value
    save_memory(mem)

def recall(key, default=None):
    return load_memory().get(key, default)

def forget(key):
    mem = load_memory()
    if key in mem:
        del mem[key]
        save_memory(mem)