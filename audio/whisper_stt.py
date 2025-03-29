# Zet spraak om naar tekst met Whisper CLI
import subprocess

def transcribe_audio(filename='input.wav'):
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
