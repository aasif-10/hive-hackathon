"""
H.I.V.E. Enhanced Scam Detector
Hybrid approach: Rule-based keywords + LLM detection
"""
import google.generativeai as genai
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Keyword categories for rule-based detection
URGENCY_KEYWORDS = ["immediately", "urgent", "today", "right now", "blocked", "suspended", "expire", "24 hours"]
AUTHORITY_KEYWORDS = ["bank", "rbi", "police", "government", "income tax", "electricity board", "trai", "customer care", "helpdesk"]
PAYMENT_KEYWORDS = ["upi", "paytm", "gpay", "phonepe", "send money", "transfer", "pay now", "account number", "ifsc", "neft", "imps"]
THREAT_KEYWORDS = ["legal action", "arrest", "case filed", "penalty", "fine", "cut", "disconnected", "warrant"]
PHISHING_KEYWORDS = ["otp", "pin", "password", "verify", "kyc", "update", "click", "download", "link", "login"]

def determine_scam_type(matched_categories):
    """Determine scam type based on matched keyword categories"""
    if matched_categories.get("payment") and matched_categories.get("authority"):
        return "bank_fraud"
    elif matched_categories.get("payment"):
        return "upi_fraud"
    elif matched_categories.get("phishing"):
        return "phishing"
    elif matched_categories.get("threat"):
        return "threat_scam"
    else:
        return "general_scam"

def check_keywords(message):
    """Step 1: Rule-based keyword detection"""
    message_lower = message.lower()
    
    matched = {
        "urgency": sum(1 for kw in URGENCY_KEYWORDS if kw in message_lower),
        "authority": sum(1 for kw in AUTHORITY_KEYWORDS if kw in message_lower),
        "payment": sum(1 for kw in PAYMENT_KEYWORDS if kw in message_lower),
        "threat": sum(1 for kw in THREAT_KEYWORDS if kw in message_lower),
        "phishing": sum(1 for kw in PHISHING_KEYWORDS if kw in message_lower)
    }
    
    total_matches = sum(matched.values())
    confidence = min(total_matches / 5.0, 1.0)
    
    return matched, confidence, total_matches

def llm_detect(message):
    """Step 2: Gemini LLM-based detection for uncertain cases"""
    try:
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        
        prompt = f"""Analyze if this message is a scam/fraud attempt targeting Indian users. 
Message: '{message}'

Look for: urgency tactics, authority impersonation (bank/police/government), 
payment requests (UPI/bank transfer), threats (account blocked/legal action), 
phishing (OTP/KYC/password).

Respond ONLY in this exact JSON format with no extra text:
{{
  "is_scam": true/false,
  "confidence": 0.0 to 1.0,
  "scam_type": "bank_fraud/upi_fraud/phishing/lottery/job_scam/other/none",
  "reasoning": "one line explanation"
}}"""

        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        # Remove markdown code blocks if present
        result_text = re.sub(r'```json\n?', '', result_text)
        result_text = re.sub(r'```\n?', '', result_text)
        
        result = json.loads(result_text)
        return result
        
    except Exception as e:
        print(f"⚠️ LLM detection error: {e}")
        return {
            "is_scam": False,
            "confidence": 0.0,
            "scam_type": "none",
            "reasoning": f"Error in LLM detection: {str(e)}"
        }

def detect_scam(message: str) -> dict:
    """
    Main scam detection function
    Returns detailed scam analysis with confidence and type
    """
    try:
        # Step 1: Rule-based keyword detection
        matched_categories, confidence, total_matches = check_keywords(message)
        
        # High confidence scam - return immediately
        if confidence >= 0.5:
            scam_type = determine_scam_type(matched_categories)
            return {
                "is_scam": True,
                "confidence": round(confidence, 2),
                "scam_type": scam_type,
                "reasoning": f"High keyword match: {total_matches} scam indicators detected",
                "method": "rule_based"
            }
        
        # Low confidence - probably not a scam
        elif confidence < 0.2:
            return {
                "is_scam": False,
                "confidence": round(1.0 - confidence, 2),
                "scam_type": "none",
                "reasoning": "No significant scam indicators found",
                "method": "rule_based"
            }
        
        # Uncertain - use LLM detection
        else:
            llm_result = llm_detect(message)
            return {
                "is_scam": llm_result.get("is_scam", False),
                "confidence": round(llm_result.get("confidence", 0.0), 2),
                "scam_type": llm_result.get("scam_type", "none"),
                "reasoning": llm_result.get("reasoning", "LLM analysis completed"),
                "method": "llm_based"
            }
            
    except Exception as e:
        return {
            "is_scam": False,
            "confidence": 0.0,
            "scam_type": "error",
            "reasoning": f"Detection error: {str(e)}",
            "method": "error"
        }
