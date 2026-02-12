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

# Import Fingerprint DB
from app.core.fingerprint_db import (
    store_fingerprint,
    find_scammer_by_identifier,
    get_all_scammers,
    get_scammer_by_fingerprint,
    get_stats,
    search_scammers,
    update_scammer_status,
    merge_scammers,
)

app = FastAPI(title="SafeTalk-AI with AI Honeypot")

# New request/response models
class HoneypotReplyRequest(BaseModel):
    scammer_message: str
    scam_type: str = "default"
    conversation_history: Optional[List[dict]] = []

class IntelligenceRequest(BaseModel):
    message: str

class FingerprintStoreRequest(BaseModel):
    intel: dict
    scam_type: str = "unknown"
    chat_id: Optional[str] = None
    message_count: int = 0

class FingerprintSearchRequest(BaseModel):
    query: str

class StatusUpdateRequest(BaseModel):
    fingerprint: str
    status: str
    notes: str = ""

class MergeRequest(BaseModel):
    fingerprint_a: str
    fingerprint_b: str

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
            "intelligence_extraction": "Regex-based",
            "fingerprint_db": "SQLite scammer profiling"
        },
        "endpoints": {
            "detect_scam": "/analyze-text",
            "honeypot_reply": "/honeypot/reply",
            "extract_intel": "/honeypot/extract",
            "fingerprint_store": "/fingerprint/store",
            "fingerprint_lookup": "/fingerprint/lookup/{identifier}",
            "fingerprint_search": "/fingerprint/search",
            "fingerprint_all": "/fingerprint/all",
            "fingerprint_stats": "/fingerprint/stats",
            "fingerprint_profile": "/fingerprint/{fingerprint_id}",
            "fingerprint_status": "/fingerprint/status",
            "fingerprint_merge": "/fingerprint/merge"
        }
    }

# ==========================================
# SCAMMER FINGERPRINT DATABASE
# ==========================================

@app.post("/fingerprint/store")
def fingerprint_store(request: FingerprintStoreRequest):
    """
    Store extracted intelligence and create/update a scammer fingerprint.
    Cross-references with existing profiles automatically.
    """
    result = store_fingerprint(
        intel=request.intel,
        scam_type=request.scam_type,
        chat_id=request.chat_id,
        message_count=request.message_count,
    )
    return result


@app.get("/fingerprint/lookup/{identifier}")
def fingerprint_lookup(identifier: str):
    """Look up a scammer by any known identifier (phone, UPI, bank account, etc.)."""
    result = find_scammer_by_identifier(identifier)
    if not result:
        return {"found": False, "message": f"No scammer found matching '{identifier}'."}
    return {"found": True, "scammer": result}


@app.post("/fingerprint/search")
def fingerprint_search(request: FingerprintSearchRequest):
    """Search scammers by partial identifier match."""
    results = search_scammers(request.query)
    return {"count": len(results), "results": results}


@app.get("/fingerprint/all")
def fingerprint_all(limit: int = 50):
    """List all known scammer profiles, ordered by threat score."""
    scammers = get_all_scammers(limit=limit)
    return {"count": len(scammers), "scammers": scammers}


@app.get("/fingerprint/stats")
def fingerprint_stats():
    """Dashboard statistics for the fingerprint database."""
    return get_stats()


@app.get("/fingerprint/{fingerprint_id}")
def fingerprint_profile(fingerprint_id: str):
    """Get a specific scammer profile by fingerprint ID."""
    result = get_scammer_by_fingerprint(fingerprint_id)
    if not result:
        return {"found": False, "message": "Scammer not found."}
    return {"found": True, "scammer": result}


@app.post("/fingerprint/status")
def fingerprint_update_status(request: StatusUpdateRequest):
    """Update a scammer's status (active / flagged / reported)."""
    success = update_scammer_status(request.fingerprint, request.status, request.notes)
    if not success:
        return {"success": False, "message": "Scammer not found or invalid status."}
    return {"success": True, "message": f"Scammer {request.fingerprint} marked as '{request.status}'."}


@app.post("/fingerprint/merge")
def fingerprint_merge(request: MergeRequest):
    """Merge two scammer profiles discovered to be the same person."""
    result = merge_scammers(request.fingerprint_a, request.fingerprint_b)
    if not result:
        return {"success": False, "message": "One or both fingerprints not found."}
    return {"success": True, "merged_profile": result}
