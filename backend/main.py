# backend/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from backend.schemas import TextInput, TextOutput
from backend.model import predict_message

# Import AI Honeypot modules
from app.core.persona_manager import select_persona
from app.core.intelligence_extractor import extract_all_intelligence
from app.core.conversation_agent import generate_reply

app = FastAPI(title="SafeTalk-AI with AI Honeypot")

# New request/response models
class HoneypotReplyRequest(BaseModel):
    scammer_message: str
    scam_type: str = "default"
    conversation_history: Optional[List[dict]] = []

class IntelligenceRequest(BaseModel):
    message: str

# ==========================================
# SAFETALK-AI SCAM DETECTION (Original)
# ==========================================
@app.post("/analyze-text", response_model=TextOutput)
def analyze_text(input_data: TextInput):
    """SafeTalk-AI scam detection using ML model"""
    result = predict_message(input_data.message)
    return result

# ==========================================
# AI HONEYPOT FEATURES
# ==========================================

@app.post("/honeypot/reply")
def honeypot_reply(request: HoneypotReplyRequest):
    """
    Generate AI honeypot reply to engage scammer
    Uses AI personas to waste scammer's time and extract intelligence
    """
    # Select persona based on scam type
    persona = select_persona(request.scam_type)
    
    # Generate reply
    reply = generate_reply(
        persona=persona,
        scammer_message=request.scammer_message,
        conversation_history=request.conversation_history
    )
    
    return {
        "reply": reply,
        "persona_name": persona["name"],
        "scam_type": request.scam_type
    }

@app.post("/honeypot/extract")
def honeypot_extract_intelligence(request: IntelligenceRequest):
    """
    Extract intelligence from scammer message
    Returns UPI IDs, phone numbers, bank accounts, phishing links
    """
    intelligence = extract_all_intelligence(request.message)
    return intelligence

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "SafeTalk-AI with AI Honeypot",
        "features": {
            "scam_detection": "ML-based (SafeTalk-AI)",
            "ai_conversation": "Gemini-powered personas",
            "intelligence_extraction": "Regex-based"
        },
        "endpoints": {
            "detect_scam": "/analyze-text",
            "honeypot_reply": "/honeypot/reply",
            "extract_intel": "/honeypot/extract"
        }
    }
