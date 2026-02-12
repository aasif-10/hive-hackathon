# backend/model.py
import joblib
import numpy as np

# Load trained components
try:
    model = joblib.load("model/scam_detector.joblib")
    vectorizer = joblib.load("model/vectorizer.joblib")
except Exception as e:
    raise RuntimeError(f"❌ Failed to load model or vectorizer: {e}")

# Label mapping
LABELS = {
    "high": "Message identified as scam",
    "scam": "Message identified as scam",
    "fraud": "Message identified as scam",
    "low": "Message appears legitimate",
    "legitimate": "Message appears legitimate",
    "safe": "Message appears legitimate"
}

def predict_message(message: str):
    vectorized = vectorizer.transform([message])
    prediction = model.predict(vectorized)[0]
    proba = np.max(model.predict_proba(vectorized))  # highest score among classes

    # Define reason based on returned label
    reason = LABELS.get(prediction.lower(), "Result undefined by AI")

    return {
        "risk": prediction,
        "confidence": round(proba, 2),
        "reason": reason
    }
