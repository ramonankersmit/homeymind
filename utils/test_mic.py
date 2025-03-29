import sounddevice as sd
import numpy as np

def audio_test(device_id):
    print(f"?? Test microfoon: device {device_id}")
    def callback(indata, frames, time_info, status):
        if status:
            print(f"[!] Status: {status}")
        volume_norm = np.linalg.norm(indata) * 10
        print("??" if volume_norm > 1 else ".", end="", flush=True)

    with sd.InputStream(
        device=device_id,
        channels=1,
        samplerate=16000,
        dtype='int16',
        callback=callback
    ):
        sd.sleep(5000)

audio_test(1)  # probeer 1, 5, 9, 14 etc.