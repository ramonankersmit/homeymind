# 🧠 HomeyMind - Slimme Spraakgestuurde AI voor je Smart Home

HomeyMind is een spraakgestuurde AI-agent gebouwd in Python.  
Hij werkt volledig offline (via Ollama) of met cloudmodellen zoals OpenAI en Groq, en stuurt je slimme huis aan via MQTT.

---

## 🚀 Features

- 🎙️ Wake word detectie ("Hey Topper") via Vosk
- 🗣️ Realtime spraakherkenning
- 🧠 LLM via OpenAI, Groq of lokaal via Ollama
- 💡 MQTT-aansturing van apparaten
- 📢 Tekst-naar-spraak via Sonos of TTS-kanaal
- 💾 Geheugen: onthoudt o.a. de laatst gekozen LLM-modus
- 🪵 Logging naar `logs/topper.log`
- 🧪 Klaar voor uitbreiding naar agent-swarms

---

## 🛠️ Installatie

### 📦 Stap 1: Voorbereiding

```bash
git clone https://github.com/jouw-gebruiker/homeymind.git
cd homeymind
```

### 🐍 Stap 2: Virtuele omgeving

```bash
python -m venv homeymind
homeymind\Scripts\activate  # Windows
```

### 📚 Stap 3: Dependencies installeren

```bash
pip install -r requirements.txt
```

### ⚙️ Stap 4: Configuratie

1. Maak een kopie van het voorbeeldbestand:
```bash
copy config.example.yaml config.yaml
```

2. Vul daarin:
   - je OpenAI- of Groq API-sleutel (optioneel)
   - welk LLM je standaard wilt gebruiken
   - MQTT-gegevens

---

## ▶️ Starten

Zorg dat je MQTT-broker draait (zoals Mosquitto), en start de agent:

```bash
python main.py
```

---

## 🎙️ Spraakcommando's

- `"Gebruik lokale AI"` → schakelt naar Ollama
- `"Gebruik cloud OpenAI"` → schakelt naar OpenAI
- `"Gebruik cloud Groq"` → schakelt naar Groq
- `"Zet woonkamerlamp aan"` → herkent intentie en stuurt MQTT-actie

---

## 💡 Tip

Gebruik `.gitignore` om `config.yaml`, `logs/`, `memory.json`, en de virtuele omgeving uit te sluiten van GitHub.

---

## 📅 Roadmap

- [x] Wake word + spraakherkenning
- [x] MQTT-aansturing
- [x] LLM-schakelaar + geheugen
- [x] Meerdere cloudproviders + fallback
- [ ] GUI-interface (bijv. via Open WebUI)
- [ ] Agent swarm integratie (CrewAI + MCP)
- [ ] Tijdsafhankelijke routines

---

## 👨‍💻 Ontwikkeld door

Een enthousiaste AI-hacker met een slimme woning 😄