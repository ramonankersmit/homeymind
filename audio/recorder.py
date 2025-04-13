"""
Audio Recording module for HomeyMind.

This module provides functionality for recording audio from the microphone
and saving it to a file. It uses sounddevice for audio capture and soundfile
for saving the audio data.
"""

import sounddevice as sd
import soundfile as sf

def record_audio_v2(duration, fs=16000):
    """
    Record audio from the microphone and return the audio data.
    
    Args:
        duration (float): Recording duration in seconds
        fs (int): Sample rate in Hz (default: 16000)
        
    Returns:
        numpy.ndarray: The recorded audio data
        
    This function:
    1. Records audio from the default microphone
    2. Waits for the recording to complete
    3. Returns the audio data
    """
    print("* Recording...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()
    print("* Done recording")
    return audio