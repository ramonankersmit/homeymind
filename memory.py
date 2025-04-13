"""
Memory management module for HomeyMind.

This module provides persistent storage functionality for the HomeyMind application.
It allows storing and retrieving key-value pairs in a JSON file, enabling the application
to remember settings and state between restarts.
"""

import json
import os

MEMORY_FILE = "memory.json"

def load_memory():
    """
    Load the memory data from the JSON file.
    
    Returns:
        dict: The memory data as a dictionary. Returns an empty dict if the file doesn't exist.
    """
    if not os.path.exists(MEMORY_FILE):
        return {}
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_memory(data):
    """
    Save the memory data to the JSON file.
    
    Args:
        data (dict): The memory data to save.
    """
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def remember(key, value):
    """
    Store a key-value pair in memory.
    
    Args:
        key (str): The key to store the value under.
        value: The value to store (must be JSON serializable).
    """
    mem = load_memory()
    mem[key] = value
    save_memory(mem)

def recall(key, default=None):
    """
    Retrieve a value from memory.
    
    Args:
        key (str): The key to retrieve the value for.
        default: The default value to return if the key doesn't exist.
        
    Returns:
        The value associated with the key, or the default value if the key doesn't exist.
    """
    return load_memory().get(key, default)

def forget(key):
    """
    Remove a key-value pair from memory.
    
    Args:
        key (str): The key to remove from memory.
    """
    mem = load_memory()
    if key in mem:
        del mem[key]
        save_memory(mem)