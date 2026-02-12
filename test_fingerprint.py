"""
Test H.I.V.E. Fingerprint Database System
"""
import requests
import json
import os
import sys

# Fix Windows encoding
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

BASE = "http://localhost:8000"

# Clean DB before test
db_path = os.path.join("data", "hive_fingerprints.db")
if os.path.exists(db_path):
    os.remove(db_path)
    print("Cleaned existing DB")

# Re-init DB
from app.core.fingerprint_db import init_db
init_db()

def test(name, response):
    status = "PASS" if response.status_code == 200 else "FAIL"
    print(f"\n{'='*60}")
    print(f"[{status}] {name} (HTTP {response.status_code})")
    print(json.dumps(response.json(), indent=2))
    return response.json()

print("=" * 60)
print("H.I.V.E. FINGERPRINT DATABASE TESTS")
print("=" * 60)

# â”€â”€ Test 1: Health check (should list fingerprint endpoints)
r = requests.get(f"{BASE}/health")
test("Health check â€” fingerprint endpoints listed", r)

# â”€â”€ Test 2: Store first scammer fingerprint
intel_1 = {
    "upiIds": ["fraud@oksbi", "scam@paytm"],
    "phoneNumbers": ["9876543210"],
    "bankAccounts": ["12345678901234"],
    "phishingLinks": ["http://sbi-verify-kyc.com"],
    "suspiciousKeywords": ["urgent", "otp", "blocked"]
}
r = requests.post(f"{BASE}/fingerprint/store", json={
    "intel": intel_1,
    "scam_type": "bank_fraud",
    "chat_id": "919876543210@c.us",
    "message_count": 5
})
fp1 = test("Store scammer #1 (bank fraud)", r)
fingerprint_1 = fp1.get("fingerprint", "")

# â”€â”€ Test 3: Store second scammer (different person)
intel_2 = {
    "upiIds": ["winner@ybl"],
    "phoneNumbers": ["8877665544"],
    "bankAccounts": [],
    "phishingLinks": ["http://lottery-prize-claim.in"],
    "suspiciousKeywords": ["winner", "prize", "click here"]
}
r = requests.post(f"{BASE}/fingerprint/store", json={
    "intel": intel_2,
    "scam_type": "lottery",
    "chat_id": "918877665544@c.us",
    "message_count": 3
})
fp2 = test("Store scammer #2 (lottery)", r)
fingerprint_2 = fp2.get("fingerprint", "")

# â”€â”€ Test 4: Re-encounter scammer #1 with new identifiers
intel_1_update = {
    "upiIds": ["fraud@oksbi"],  # existing
    "phoneNumbers": ["9876543210", "7766554433"],  # one new
    "bankAccounts": [],
    "phishingLinks": [],
    "suspiciousKeywords": ["verify", "kyc"]
}
r = requests.post(f"{BASE}/fingerprint/store", json={
    "intel": intel_1_update,
    "scam_type": "upi_fraud",  # new scam type
    "chat_id": "917766554433@c.us",
    "message_count": 4
})
fp1_updated = test("Re-encounter scammer #1 (should update, not create new)", r)
assert fp1_updated.get("fingerprint") == fingerprint_1, "Fingerprint should match!"
assert fp1_updated.get("encounter_count", 0) >= 2, "Encounter count should increase!"
assert fp1_updated.get("is_new_scammer") == False, "Should NOT be new!"
print("  âœ“ Cross-reference worked â€” same scammer re-identified!")

# â”€â”€ Test 5: Lookup by phone number
r = requests.get(f"{BASE}/fingerprint/lookup/9876543210")
test("Lookup by phone number", r)

# â”€â”€ Test 6: Lookup by UPI ID
r = requests.get(f"{BASE}/fingerprint/lookup/fraud@oksbi")
test("Lookup by UPI ID", r)

# â”€â”€ Test 7: Lookup unknown identifier
r = requests.get(f"{BASE}/fingerprint/lookup/0000000000")
test("Lookup unknown identifier (should be not found)", r)

# â”€â”€ Test 8: Search partial match
r = requests.post(f"{BASE}/fingerprint/search", json={"query": "fraud"})
test("Search partial match 'fraud'", r)

# â”€â”€ Test 9: Get all scammers
r = requests.get(f"{BASE}/fingerprint/all")
result = test("List all scammers", r)
assert result["count"] == 2, f"Expected 2 scammers, got {result['count']}"
print("  âœ“ Both scammers in database!")

# â”€â”€ Test 10: Get stats
r = requests.get(f"{BASE}/fingerprint/stats")
stats = test("DB Statistics", r)
assert stats["total_scammers"] == 2
print("  âœ“ Stats correct!")

# â”€â”€ Test 11: Get profile by fingerprint
r = requests.get(f"{BASE}/fingerprint/{fingerprint_1}")
test("Get profile by fingerprint", r)

# â”€â”€ Test 12: Flag scammer
r = requests.post(f"{BASE}/fingerprint/status", json={
    "fingerprint": fingerprint_2,
    "status": "flagged",
    "notes": "High confidence lottery scam"
})
test("Flag scammer #2", r)

# â”€â”€ Test 13: Report scammer
r = requests.post(f"{BASE}/fingerprint/status", json={
    "fingerprint": fingerprint_1,
    "status": "reported",
    "notes": "Reported to cybercrime portal"
})
test("Report scammer #1", r)

# â”€â”€ Test 14: Verify updated statuses in stats
r = requests.get(f"{BASE}/fingerprint/stats")
stats = test("Stats after status updates", r)
assert stats["flagged"] == 1, "1 scammer should be flagged"
assert stats["reported"] == 1, "1 scammer should be reported"
print("  âœ“ Status updates reflected correctly!")

# â”€â”€ Test 15: Full pipeline â€” detect + extract + fingerprint
print(f"\n{'='*60}")
print("FULL PIPELINE TEST: detect â†’ extract â†’ fingerprint")
print("="*60)

scam_msg = "Your SBI account is blocked! Send Rs.50 to verifykyc@okhdfc or call 9911223344 immediately."

# Step 1: Detect
r = requests.post(f"{BASE}/analyze-text", json={"message": scam_msg})
detection = test("Step 1: ML Detection", r)

# Step 2: Extract
r = requests.post(f"{BASE}/honeypot/extract", json={"message": scam_msg})
intel = test("Step 2: Extract Intelligence", r)

# Step 3: Fingerprint
r = requests.post(f"{BASE}/fingerprint/store", json={
    "intel": intel,
    "scam_type": "bank_fraud",
    "chat_id": "919911223344@c.us",
    "message_count": 1
})
fp = test("Step 3: Store Fingerprint", r)

print(f"\n{'='*60}")
print(f"ALL TESTS COMPLETE")
print(f"Scammers in DB: check /fingerprint/stats")
print(f"{'='*60}")

