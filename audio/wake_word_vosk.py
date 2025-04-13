"""
Wake Word Detection module for HomeyMind.

This module provides wake word detection functionality using the Vosk speech recognition
engine. It continuously listens to the microphone input and triggers when the specified
wake word is detected.
"""

# Wake word detectie via Vosk met regex-matching, logging en TTS-reactie
from vosk import Model, KaldiRecognizer
import sounddevice as sd
import queue
import json
import re
from homey.mqtt_client import publish_tts
import yaml

def wait_for_wake_word(model_path='models/vosk-model-nl', wake_word='topper', device=1):
    """
    Wait for the wake word to be detected in the audio input.
    
    Args:
        model_path (str): Path to the Vosk model directory
        wake_word (str): The word to listen for
        device (int): The audio device index to use
        
    Returns:
        bool: True if wake word was detected, False if interrupted
        
    This function:
    1. Loads the Vosk model
    2. Sets up audio input stream
    3. Processes audio and checks for wake word
    4. Triggers TTS response when wake word is detected
    5. Returns after wake word is detected
    """
    # Config laden voor TTS
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    model = Model(model_path)
    recognizer = KaldiRecognizer(model, 16000)
    audio_q = queue.Queue()

    def callback(indata, frames, time_info, status):
        """
        Audio callback function that processes incoming audio data.
        
        Args:
            indata: Input audio data
            frames: Number of frames
            time_info: Time information
            status: Status flags
        """
        if status:
            print(f"[Audio status] {status}")
        audio_q.put(bytes(indata))

    print("* Luisteren naar wake word...")
    with sd.RawInputStream(
        samplerate=16000,
        blocksize=8000,
        device=device,
        dtype='int16',
        channels=1,
        callback=callback
    ):
        while True:
            try:
                data = audio_q.get()
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "").lower()
                    if re.search(rf"\b{wake_word}\b", text):
                        print("* Wake word gedetecteerd!")
                        publish_tts("Oké, ik luister", config)
                        return True
            except KeyboardInterrupt:
                return False