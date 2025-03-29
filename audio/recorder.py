import sounddevice as sd
import soundfile as sf

def record_audio(filename, duration, fs=16000):
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()
    sf.write(filename, audio, fs)