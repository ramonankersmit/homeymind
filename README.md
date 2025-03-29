
# HomeyMind

Jouw eigen spraakgestuurde AI-assistent voor Homey Pro, volledig lokaal of hybride (OpenAI, Groq). Zeg "Hey Topper" en automatiseer alles in huis. 🎤🏡🤖

---

## 🚀 Installatie

1. Clone de repository:

```bash
git clone https://github.com/ramonankersmit/homeymind.git
cd homeymind
```

2. Maak een virtuele omgeving:

```bash
python -m venv homeymind
homeymind\Scripts\activate
```

3. Installeer afhankelijkheden:

```bash
pip install -r requirements.txt
```

4. Kopieer het voorbeeldconfiguratiebestand:

```bash
copy config.example.yaml config.yaml
```

5. Vul je `config.yaml` aan met:
   - je OpenAI of Groq sleutel
   - MQTT host (bijv. Homey IP)
   - modelvoorkeur (`local`, `openai`, `groq`)

---

## 🛠️ Extra installatie na het clonen

### 📦 1. Vosk spraakmodel installeren

```bash
mkdir models
curl -L -o vosk-model-nl.zip https://alphacephei.com/vosk/models/vosk-model-nl-0.22.zip
tar -xf vosk-model-nl.zip -C models
rename "models\vosk-model-nl-0.22" "models\vosk-model-nl"
```

Zorg dat het pad daarna is:
```
C:\Projects\HomeyMind\models\vosk-model-nl
```

---

### 🤖 2. Ollama lokaal model installeren

Als je lokaal een LLM wilt draaien:

```bash
ollama run mistral
```

Zorg ervoor dat dit overeenkomt met je `config.yaml`:

```yaml
llm:
  provider: local
  local_model: mistral
```

Meer modellen: https://ollama.com/library

---

## 🧪 Starten

```bash
python main.py
```

Zeg "Hey Topper", geef een opdracht en laat de AI je helpen met je huis.

---

## 💡 Roadmap

- [x] Wake word met Vosk
- [x] Streaming transcriptie (Whisper)
- [x] MQTT-interactie met Homey
- [x] TTS voor Sonos
- [x] Wisselen tussen lokale/cloud LLM's
- [x] OpenAI & Groq ondersteuning
- [ ] GUI (Open WebUI integratie)
- [ ] CrewAI agent swarm
- [ ] Memory en logboek
- [ ] Suggesties & zelfbedachte acties

---

## 🧠 Gemaakt door Ramon & GPT – voor een slimmer huis.
