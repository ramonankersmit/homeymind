"""
Audio Transcription module for HomeyMind.

This module provides real-time speech-to-text transcription functionality using the Vosk
speech recognition engine. It continuously listens to the microphone input and transcribes
the audio in real-time.
"""

from vosk import Model, KaldiRecognizer
import sounddevice as sd
import queue
import json

def transcribe_audio(model_path="models/vosk-model-nl", samplerate=16000):
    """
    Transcribe audio input in real-time using Vosk speech recognition.
    
    Args:
        model_path (str): Path to the Vosk model directory
        samplerate (int): Audio sample rate in Hz
        
    Returns:
        str: The transcribed text
        
    This function:
    1. Loads the Vosk model
    2. Sets up audio input stream
    3. Continuously processes audio and transcribes speech
    4. Returns the transcribed text when a complete utterance is detected
    """
    model = Model(model_path)
    recognizer = KaldiRecognizer(model, samplerate)
    audio_q = queue.Queue()

    def callback(indata, frames, time, status):
        """
        Audio callback function that processes incoming audio data.
        
        Args:
            indata: Input audio data
            frames: Number of frames
            time: Time information
            status: Status flags
        """
        if status:
            print("[Audio status]", status)
        audio_q.put(bytes(indata))

    print("* [Streaming] Luisteren voor realtime transcriptie...")

    text_result = ""
    with sd.RawInputStream(samplerate=samplerate, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        while True:
            data = audio_q.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text_result = result.get("text", "").strip()
                if text_result:
                    print(f"* [Streaming] Herkende tekst: {text_result}")
                    return text_result
            else:
                partial = json.loads(recognizer.PartialResult()).get("partial", "")
                if partial:
                    print(f"[DEBUG] Herkende tekst: {partial}", end="\r")