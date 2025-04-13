"""
Audio Recording module for HomeyMind.

This module provides functionality for recording audio from the microphone
and saving it to a file. It uses sounddevice for audio capture and soundfile
for saving the audio data.
"""

import sounddevice as sd
import soundfile as sf

def record_audio(filename, duration, fs=16000):
    """
    Record audio from the microphone and save it to a file.
    
    Args:
        filename (str): Path to save the audio file
        duration (float): Recording duration in seconds
        fs (int): Sample rate in Hz (default: 16000)
        
    This function:
    1. Records audio from the default microphone
    2. Waits for the recording to complete
    3. Saves the audio to the specified file
    """
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()
    sf.write(filename, audio, fs)