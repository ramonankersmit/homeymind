def suggest_closest_devices(device, known_devices, max_suggestions=3):
    from difflib import get_close_matches
    return get_close_matches(device, known_devices, n=max_suggestions, cutoff=0.5)