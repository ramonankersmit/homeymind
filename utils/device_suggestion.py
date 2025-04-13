"""
Device Suggestion module for HomeyMind.

This module provides functionality for suggesting similar device names when
a user requests an unknown device. It uses string similarity matching to
find the closest matches from the list of known devices.
"""

def suggest_closest_devices(device, known_devices, max_suggestions=3):
    """
    Suggest the closest matching device names from the list of known devices.
    
    Args:
        device (str): The unknown device name to find matches for
        known_devices (list): List of known device names
        max_suggestions (int): Maximum number of suggestions to return
        
    Returns:
        list: List of suggested device names, sorted by similarity
    """
    from difflib import get_close_matches
    return get_close_matches(device, known_devices, n=max_suggestions, cutoff=0.5)