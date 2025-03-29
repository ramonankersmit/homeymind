# Wake word detectie via Vosk met regex-matching, logging en TTS-reactie
from vosk import Model, KaldiRecognizer
import sounddevice as sd
import queue
import json
import re
from homey.mqtt_client import publish_tts
import yaml

def wait_for_wake_word(model_path='models/vosk-model-nl', wake_word='topper', device=1):
    # Config laden voor TTS
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    model = Model(model_path)
    recognizer = KaldiRecognizer(model, 16000)
    audio_q = queue.Queue()

    def callback(indata, frames, time_info, status):
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
            data = audio_q.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").lower()
                print(f"[DEBUG] Herkende tekst: {text}. Zoeken naar: {wake_word}")
                if re.search(rf"\b{wake_word}\b", text):
                    print("* Wake word gedetecteerd!")
                    publish_tts("Oké, ik luister", config)
                    break