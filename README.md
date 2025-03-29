
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
<project_path>\HomeyMind\models\vosk-model-nl
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

### 📡 3. MQTT instellen (vereist)

De AI-agent gebruikt MQTT om met Homey te communiceren.



#### ✅ Aanbevolen: Homey als MQTT Broker

Gebruik de [MQTT Broker app](https://homey.app/nl-nl/app/nl.scanno.mqttbroker/MQTT-Broker/) op je Homey Pro:

1. Installeer de app op je Homey
2. Start de broker via de app
3. De broker luistert standaard op poort `1883`
4. Vul in je `config.yaml` het IP van Homey in:

```yaml
mqtt:
  host: 192.168.1.150  # Vervang dit door het IP van jouw Homey
  port: 1883
  topic_prefix: ai/
```

Zo praat je AI-agent direct met Homey zonder extra apps.


#### 🔘 Alternatief – Homey als MQTT client:
1. Installeer in Homey de MQTT Client app
2. Stel je MQTT broker IP/poort in (bijv. `192.168.1.150:1883`)
3. Voeg een flow toe die luistert op topic `ai/#`

#### 🔘 Optie B – Lokale MQTT broker installeren (optioneel):

Installeer Mosquitto (Windows):

```bash
winget install mosquitto
```

Start de broker met:

```bash
mosquitto -v
```

#### ⚙️ config.yaml

Zorg dat je brokerinstellingen kloppen:

```yaml
mqtt:
  host: localhost
  port: 1883
  topic_prefix: ai/
```

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
- [ ] Intent recognition Agent
- [ ] Memory en logboek
- [ ] Suggesties & zelfbedachte acties

---

## 🧠 Ontwikkeld voor slimme huisautomatisering met lokale intelligentie en maximale controle.
