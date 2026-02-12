# SafeTalk-AI with AI Honeypot Integration

## 🎯 What This Does

**SafeTalk-AI** now has AI honeypot capabilities! When a scam is detected, the system can automatically engage the scammer with realistic AI personas to:
- ✅ Waste scammer's time
- ✅ Extract intelligence (UPI IDs, phone numbers, links)
- ✅ Gather evidence for reporting
- ✅ Protect real victims

## 🔄 How It Works

```
1. Message comes in → SafeTalk-AI ML model detects if it's a scam
2. If scam detected → AI honeypot activates with realistic persona
3. AI persona engages scammer → Asks questions, pretends to be confused
4. System extracts intelligence → UPI IDs, phone numbers, links
5. Evidence collected → Can be reported to authorities
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install google-generativeai python-dotenv
```

### 2. Get Gemini API Key
- Go to: https://aistudio.google.com/apikey
- Create a free API key
- Add to `.env`:
```env
GEMINI_API_KEY=your_actual_key_here
API_KEY=hive-secret-key-2025
```

### 3. Start Server
```bash
python -m uvicorn backend.main:app --reload --port 8000
```

### 4. Test the System
```bash
python test_honeypot_simple.py
```

## 📡 API Endpoints

### 1. Detect Scam (SafeTalk-AI)
```http
POST /analyze-text
Content-Type: application/json

{
  "message": "Your bank account will be blocked. Send OTP now."
}
```

**Response:**
```json
{
  "risk": "scam",
  "confidence": 0.90,
  "reason": "Message identified as scam"
}
```

### 2. Generate AI Honeypot Reply
```http
POST /honeypot/reply
Content-Type: application/json

{
  "scammer_message": "Send Rs.10 to verify@okhdfc now!",
  "scam_type": "bank_fraud",
  "conversation_history": []
}
```

**Response:**
```json
{
  "reply": "Ayyo, I am trying but this phone is confusing me. Can you explain slowly?",
  "persona_name": "Ramesh (Panicked Elder)",
  "scam_type": "bank_fraud"
}
```

### 3. Extract Intelligence
```http
POST /honeypot/extract
Content-Type: application/json

{
  "message": "Call 9876543210 or send to scammer@okhdfc"
}
```

**Response:**
```json
{
  "upiIds": ["scammer@okhdfc"],
  "phoneNumbers": ["9876543210"],
  "bankAccounts": [],
  "phishingLinks": [],
  "suspiciousKeywords": ["send"]
}
```

## 🎭 Available AI Personas

The system uses realistic personas based on scam type:

1. **bank_fraud** → Ramesh (68, Panicked Elder)
2. **upi_fraud** → Priya (42, Worried Housewife)
3. **phishing** → Arjun (22, Gullible Student)
4. **lottery** → Suresh (48, Greedy Businessman)
5. **default** → Kavitha (35, Cautious Teacher)

Each persona has:
- Unique personality and background
- Realistic speech patterns
- Strategic goals to extract scammer info

## 💻 Usage Example in Code

```python
import requests

# Step 1: Detect scam
response = requests.post("http://localhost:8000/analyze-text", 
    json={"message": "Your bank account blocked. Send OTP now!"})
result = response.json()

if "scam" in result['risk'].lower():
    # Step 2: Engage with AI honeypot
    honeypot = requests.post("http://localhost:8000/honeypot/reply",
        json={
            "scammer_message": "Send OTP 123456",
            "scam_type": "bank_fraud"
        })
    
    ai_reply = honeypot.json()['reply']
    print(f"AI Response: {ai_reply}")
    
    # Step 3: Extract intelligence
    intel = requests.post("http://localhost:8000/honeypot/extract",
        json={"message": "Send OTP 123456"})
    
    print(f"Extracted: {intel.json()}")
```

## 🔧 Configuration

### Scam Type Mapping
You can customize which persona activates for different scams:
- `bank_fraud` - Banking/account security scams
- `upi_fraud` - UPI payment scams
- `phishing` - Credential theft attempts
- `lottery` - Prize/lottery scams
- `default` - Generic scams

## ⚠️ Important Notes

1. **API Key Required**: Gemini API key needed for AI conversations
2. **Free Tier**: Gemini has generous free tier limits
3. **Privacy**: No real user data is ever shared with scammers
4. **Safety**: System uses fake OTPs and details (never real ones)

## 🎯 Use Cases

### For Individuals
- Automatically respond to scam messages
- Waste scammer's time while you're busy
- Collect evidence for reporting

### For Organizations
- Protect customers from scams
- Gather scam intelligence
- Build databases of scammer tactics
- Report to authorities with evidence

### For Researchers
- Study scam tactics and psychology
- Build better detection models
- Understand social engineering techniques

## 📊 System Architecture

```
┌─────────────────┐
│   WhatsApp Bot  │ (Optional)
└────────┬────────┘
         │
         v
┌─────────────────┐
│  SafeTalk-AI    │ ML-based scam detection
│  (ML Model)     │ 
└────────┬────────┘
         │
         v
      Scam? Yes
         │
         v
┌─────────────────┐
│  AI Honeypot    │ Gemini-powered personas
│  (Gemini API)   │ Realistic conversations
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Intelligence   │ Extract UPI, phones, links
│  Extractor      │ Regex-based extraction
└─────────────────┘
```

## 🤝 Integration with WhatsApp

The system can work with WhatsApp Web bot (coming soon):
1. Bot receives message
2. SafeTalk-AI checks if it's a scam
3. If scam: AI honeypot generates reply
4. Bot sends AI reply back to scammer
5. Intelligence extracted and logged

## 📝 License

Same as SafeTalk-AI (MIT License)

## 🙏 Credits

- **SafeTalk-AI**: Original scam detection
- **Google Gemini**: AI conversation engine
- **H.I.V.E. Concept**: Honeypot intelligence framework
