<p align="center">
  <h1 align="center">H.I.V.E.</h1>
  <h3 align="center">Heuristic Intelligence & Virtual Entrapment</h3>
  <p align="center">AI-Powered Scam Honeypot System built on SafeTalk-AI</p>
  <p align="center">
    <img alt="Python" src="https://img.shields.io/badge/python-3.11+-blue"/>
    <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.100+-green"/>
    <img alt="Gemini" src="https://img.shields.io/badge/Google%20Gemini-2.5--flash-orange"/>
    <img alt="License" src="https://img.shields.io/badge/license-MIT-brightgreen"/>
    <img alt="Status" src="https://img.shields.io/badge/Status-Hackathon%20Ready-blueviolet"/>
  </p>
</p>

---

## The Problem

Millions of people fall victim to phone/messaging scams every year. Scammers use urgency, fear, and social engineering to steal money and personal information. Current solutions only **block or warn** — they don't fight back.

## Our Solution

**H.I.V.E.** doesn't just detect scams — it **engages scammers with realistic AI personas** to waste their time, extract their identities (UPI IDs, phone numbers, bank details), and gather evidence for reporting.

Built on top of SafeTalk-AI's ML-based scam detection, H.I.V.E. adds an intelligent honeypot layer that turns the tables on scammers.

---

## How It Works

```
Scammer sends message
        │
        ▼
┌─────────────────────┐
│  SafeTalk-AI ML      │  ← Random Forest + TF-IDF classifier
│  Scam Detection      │     Detects scam vs legitimate
└────────┬────────────┘
         │ scam detected
         ▼
┌─────────────────────┐
│  H.I.V.E. Honeypot  │  ← Gemini AI-powered personas
│  Auto-Engagement     │     Engages scammer in conversation
└────────┬────────────┘
         │ every turn
         ▼
┌─────────────────────┐
│  Intelligence        │  ← Regex-based extraction
│  Extraction          │     UPI IDs, phone numbers, links
└─────────────────────┘
```

1. **Detect** — ML model classifies incoming messages as scam or legitimate
2. **Engage** — AI persona (confused retiree, worried housewife, etc.) replies naturally to the scammer
3. **Extract** — System captures UPI IDs, phone numbers, phishing links, and suspicious keywords from the conversation
4. **Report** — Collected intelligence can be forwarded to authorities

---

## Key Features

| Feature                     | Description                                                                                           |
| --------------------------- | ----------------------------------------------------------------------------------------------------- |
| **ML Scam Detection**       | Random Forest classifier with TF-IDF vectorization identifies scam messages with confidence scores    |
| **AI Honeypot Personas**    | 5 unique personas powered by Google Gemini that engage scammers in realistic multi-turn conversations |
| **Intelligence Extraction** | Automatically captures UPI IDs, phone numbers, bank accounts, and phishing links                      |
| **WhatsApp Integration**    | Full WhatsApp Web bot that auto-detects and engages scammers in real-time                             |
| **Audio Transcription**     | Voice messages transcribed via Whisper and analyzed for scam content                                  |
| **No Fallback Responses**   | Every reply is AI-generated and unique — no canned responses                                          |

---

## Tech Stack

- **Backend:** Python, FastAPI, Uvicorn
- **ML Model:** scikit-learn (Random Forest + TF-IDF)
- **AI Conversation:** Google Gemini 2.5 Flash via `google-genai`
- **WhatsApp Bot:** Node.js, whatsapp-web.js, Puppeteer
- **Audio:** OpenAI Whisper
- **Data:** In-memory (Python dicts), joblib model persistence

---

## Project Structure

```
├── backend/
│   ├── main.py                 # FastAPI app with all endpoints
│   ├── model.py                # ML prediction (scam/legitimate)
│   ├── schemas.py              # Pydantic request/response models
│   └── train_model.py          # Train the Random Forest classifier
├── app/core/
│   ├── conversation_agent.py   # Gemini-powered AI conversation engine
│   ├── persona_manager.py      # 5 AI personas with system prompts
│   ├── intelligence_extractor.py # Regex extraction (UPI, phones, links)
│   └── scam_detector.py        # Rule-based detection (supplementary)
├── whatsapp-bot/
│   └── whatsapp-web.js         # WhatsApp bot with honeypot integration
├── data/
│   └── messages.csv            # Training dataset
├── model/
│   ├── scam_detector.joblib    # Trained ML model
│   └── vectorizer.joblib       # TF-IDF vectorizer
├── transcribe.py               # Whisper audio transcription
├── .env                        # API keys (not committed)
└── requirements.txt            # Python dependencies
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Google Gemini API key ([get one free](https://aistudio.google.com/apikey))

### 1. Clone & Setup

```bash
git clone https://github.com/aasif-10/hive-hackathon.git
cd hive-hackathon

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure API Key

Create a `.env` file in the root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
API_KEY=hive-secret-key-2025
```

### 3. Train the ML Model

```bash
python backend/train_model.py
```

### 4. Start the Backend

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 5. Start the WhatsApp Bot (optional)

```bash
cd whatsapp-bot
npm install
node whatsapp-web.js
```

Scan the QR code at `http://localhost:3000/qr` with your WhatsApp.

### 6. Test

```bash
python test_terminal.py
```

---

## API Endpoints

| Method | Endpoint            | Description                          |
| ------ | ------------------- | ------------------------------------ |
| `POST` | `/analyze-text`     | Detect scam using ML model           |
| `POST` | `/honeypot/reply`   | Generate AI persona reply to scammer |
| `POST` | `/honeypot/extract` | Extract intelligence from message    |
| `GET`  | `/health`           | Service health check                 |

### Example: Detect + Engage

```bash
# Step 1: Detect scam
curl -X POST http://localhost:8000/analyze-text \
  -H "Content-Type: application/json" \
  -d '{"message": "Your bank account will be blocked. Send OTP now."}'

# Step 2: Engage with honeypot
curl -X POST http://localhost:8000/honeypot/reply \
  -H "Content-Type: application/json" \
  -d '{"scammer_message": "Send Rs.10 to verify@okhdfc now!", "scam_type": "bank_fraud", "conversation_history": []}'
```

---

## AI Personas

| Persona     | Role                     | Scam Type  | Strategy                                             |
| ----------- | ------------------------ | ---------- | ---------------------------------------------------- |
| **Ramesh**  | Worried Retiree, 68      | Bank Fraud | Confused with tech, asks scammer to repeat details   |
| **Priya**   | Unsure Housewife, 42     | UPI Fraud  | Husband not home, asks for WhatsApp details          |
| **Arjun**   | Eager Student, 22        | Phishing   | Interested but wants to verify with parents          |
| **Suresh**  | Skeptical Shopkeeper, 48 | Lottery    | Asks for proof and refund bank details               |
| **Kavitha** | Careful Teacher, 35      | Default    | Cooperative but very slow, needs everything repeated |

All personas speak in plain, natural English — no regional words, no robotic responses.

---

## Sample Conversation

> **Scammer:** Your bank account has been compromised. Send OTP immediately to verify.
>
> **Ramesh:** Oh dear, compromised? That sounds serious. I'm not very good with these things. Could you give me your name, so I know who I'm speaking with?
>
> **Scammer:** Send Rs.10 to verify@sbifraud to confirm your identity.
>
> **Ramesh:** Rs.10? I don't think I've ever done that before. Is that through that phone app thing? I'm not very good with those.
>
> **Scammer:** Just call our senior manager at 8899776655.
>
> **Ramesh:** Oh, a senior manager? 8899776655, you said? Can you repeat that number for me, please? I need to write it down carefully.

**Intelligence Extracted:** UPI ID `verify@sbifraud`, Phone `8899776655`

---

## WhatsApp Bot Commands

| Command         | Action                                       |
| --------------- | -------------------------------------------- |
| `!status`       | Check bot status and active sessions         |
| `!honeypot on`  | Enable auto-engage mode                      |
| `!honeypot off` | Disable — alerts only                        |
| `!intel`        | Show extracted intelligence for current chat |
| `!reset`        | Clear honeypot session                       |

---

## Team

Built for a national hackathon by **Team H.I.V.E.**

## License

MIT License
