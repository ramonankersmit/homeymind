"""
Audio Transcription module for HomeyMind.

This module provides speech-to-text transcription functionality using the Vosk
speech recognition engine.
"""

from vosk import Model, KaldiRecognizer
import sounddevice as sd
import queue
import json
import numpy as np

def transcribe_audio(audio_data, model_path="models/vosk-model-nl", samplerate=16000):
    """
    Transcribe audio data using Vosk speech recognition.
    
    Args:
        audio_data (numpy.ndarray): The audio data to transcribe
        model_path (str): Path to the Vosk model directory
        samplerate (int): Audio sample rate in Hz
        
    Returns:
        str: The transcribed text
        
    This function:
    1. Loads the Vosk model
    2. Processes the audio data
    3. Returns the transcribed text
    """
    model = Model(model_path)
    recognizer = KaldiRecognizer(model, samplerate)
    
    # Convert audio data to bytes
    audio_bytes = audio_data.tobytes()
    
    # Process audio data
    if recognizer.AcceptWaveform(audio_bytes):
        result = json.loads(recognizer.Result())
        text = result.get("text", "").strip()
        if text:
            print(f"* Herkende tekst: {text}")
            return text
    
    return ""