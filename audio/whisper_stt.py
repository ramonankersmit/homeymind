"""
Whisper Speech-to-Text module for HomeyMind.

This module provides speech-to-text transcription functionality using the Whisper
CLI tool. It processes audio files and returns the transcribed text.
"""

# Zet spraak om naar tekst met Whisper CLI
import subprocess

def transcribe_audio(filename='input.wav'):
    """
    Transcribe audio file using Whisper CLI.
    
    Args:
        filename (str): Path to the audio file to transcribe
        
    Returns:
        str: The transcribed text, or empty string if transcription fails
        
    This function:
    1. Runs Whisper CLI on the audio file
    2. Processes the output to extract the transcribed text
    3. Returns the transcribed text or handles errors
    """
    print("* Spraak omzetten...")
    try:
        result = subprocess.run(["whisper", filename, "--language", "nl", "--model", "base"], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if "[00:00.000 -->" in line:
                tekst = line.split(']')[-1].strip()
                print(f"* Herkende tekst: {tekst}")
                return tekst
    except Exception as e:
        print(f"Whisper fout: {e}")
        return ""
