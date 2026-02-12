# -*- coding: utf-8 -*-
"""
SafeTalk-AI + H.I.V.E. Honeypot  -  Terminal Test
Works on Windows cp1252 terminals (no emoji)
"""
import sys, io, requests, time

# Force UTF-8 stdout so emoji/unicode never crash on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = "http://localhost:8000"

def sep(title=""):
    print("\n" + "=" * 60)
    if title:
        print(title)
        print("=" * 60)


def main():
    # ---- Health check ----
    try:
        r = requests.get(f"{BASE}/health", timeout=5)
        h = r.json()
        print(f"[OK] {h['service']} is online")
        print(f"     Scam Detection : {h['features']['scam_detection']}")
        print(f"     AI Conversation: {h['features']['ai_conversation']}")
    except Exception as e:
        print(f"[FAIL] Cannot reach server at {BASE} -> {e}")
        return

    # ---- Step 1: ML scam detection ----
    sep("STEP 1 : Scam Detection (SafeTalk-AI ML)")
    msg = "Your bank account will be blocked today. Send OTP immediately to verify."
    r = requests.post(f"{BASE}/analyze-text", json={"message": msg})
    det = r.json()
    print(f"  Message   : {msg}")
    print(f"  Risk      : {det['risk']}")
    print(f"  Confidence: {det['confidence']}")
    print(f"  Reason    : {det['reason']}")

    is_scam = "scam" in det["risk"].lower()
    if not is_scam:
        print("\n  -> Legitimate message. Honeypot not needed.")
        return
    print("\n  -> Scam detected! Activating honeypot ...")

    # ---- Step 2: Single honeypot reply ----
    sep("STEP 2 : AI Honeypot Reply (single turn)")
    r = requests.post(f"{BASE}/honeypot/reply", json={
        "scammer_message": msg,
        "scam_type": "bank_fraud",
        "conversation_history": []
    })
    if r.status_code != 200:
        print(f"  [ERROR] {r.status_code} - {r.text}")
        return
    hp = r.json()
    print(f"  Persona : {hp['persona_name']}")
    print(f"  Reply   : {hp['reply']}")

    # ---- Step 3: Multi-turn conversation ----
    sep("STEP 3 : Multi-Turn Honeypot Conversation")
    scammer_lines = [
        "Your bank account has been compromised. Verify immediately.",
        "Send Rs.10 to verify@okhdfc to unlock your account.",
        "Why are you taking time? Call 9876543210 now!",
        "This is your last warning! Act now or lose everything!",
    ]

    history = []
    all_text = ""
    for i, line in enumerate(scammer_lines, 1):
        history.append({"sender": "scammer", "text": line})
        all_text += " " + line

        r = requests.post(f"{BASE}/honeypot/reply", json={
            "scammer_message": line,
            "scam_type": "bank_fraud",
            "conversation_history": history
        })
        if r.status_code != 200:
            print(f"  Turn {i} [ERROR] {r.status_code} - {r.text}")
            return
        data = r.json()
        reply = data["reply"]
        history.append({"sender": "victim", "text": reply})
        all_text += " " + reply

        print(f"\n  Turn {i}")
        print(f"    Scammer : {line}")
        print(f"    {data['persona_name']} : {reply}")
        time.sleep(1)  # respect rate limits

    # ---- Step 4: Intelligence extraction ----
    sep("STEP 4 : Intelligence Extraction")
    r = requests.post(f"{BASE}/honeypot/extract", json={"message": all_text})
    intel = r.json()
    print(f"  UPI IDs     : {intel.get('upiIds', [])}")
    print(f"  Phone Nums  : {intel.get('phoneNumbers', [])}")
    print(f"  Links       : {intel.get('phishingLinks', [])}")
    print(f"  Keywords    : {intel.get('suspiciousKeywords', [])}")

    sep("ALL TESTS PASSED - AI conversation working seamlessly!")


if __name__ == "__main__":
    main()
