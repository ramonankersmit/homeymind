from vosk import Model, KaldiRecognizer
import sounddevice as sd
import queue
import json

def transcribe_audio(model_path="models/vosk-model-nl", samplerate=16000):
    model = Model(model_path)
    recognizer = KaldiRecognizer(model, samplerate)
    audio_q = queue.Queue()

    def callback(indata, frames, time, status):
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