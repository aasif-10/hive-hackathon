"""
Test H.I.V.E. Honeypot Features
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_honeypot_detect():
    """Test H.I.V.E. enhanced scam detection"""
    print("\n" + "="*60)
    print("TEST 1: H.I.V.E. Enhanced Scam Detection")
    print("="*60)
    
    test_messages = [
        "Your bank account will be blocked today. Send OTP immediately.",
        "Send Rs.10 to badguy@okhdfc to verify your account now!",
        "Hi, how are you doing today?"
    ]
    
    for msg in test_messages:
        print(f"\n📩 Testing: \"{msg[:50]}...\"")
        response = requests.post(
            f"{BASE_URL}/honeypot/detect",
            json={"message": msg}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   🎯 Is Scam: {result['is_scam']}")
            print(f"   📊 Confidence: {result['confidence']}")
            print(f"   🏷️  Type: {result['scam_type']}")
            print(f"   💬 Reasoning: {result['reasoning']}")
            print(f"   ⚙️  Method: {result['method']}")
        else:
            print(f"   ❌ Error: {response.status_code}")

def test_intelligence_extraction():
    """Test intelligence extraction"""
    print("\n" + "="*60)
    print("TEST 2: Intelligence Extraction")
    print("="*60)
    
    test_message = "Send Rs.100 to scammer@okhdfc or call 9876543210. Download from fakebank-verify.com"
    
    print(f"\n📩 Extracting from: \"{test_message}\"")
    response = requests.post(
        f"{BASE_URL}/honeypot/extract",
        json={"message": test_message}
    )
    
    if response.status_code == 200:
        intel = response.json()
        print(f"\n📊 Extracted Intelligence:")
        print(f"   💳 UPI IDs: {intel['upiIds']}")
        print(f"   📞 Phone Numbers: {intel['phoneNumbers']}")
        print(f"   🏦 Bank Accounts: {intel['bankAccounts']}")
        print(f"   🔗 Phishing Links: {intel['phishingLinks']}")
        print(f"   ⚠️  Keywords: {intel['suspiciousKeywords']}")
    else:
        print(f"   ❌ Error: {response.status_code}")

def test_honeypot_conversation():
    """Test honeypot conversation"""
    print("\n" + "="*60)
    print("TEST 3: Honeypot Conversation (AI Persona)")
    print("="*60)
    
    scenarios = [
        {
            "scam_type": "bank_fraud",
            "message": "Your bank account will be blocked. Verify immediately by sending OTP."
        },
        {
            "scam_type": "upi_fraud",
            "message": "Send Rs.10 to verify@okhdfc to avoid account suspension."
        }
    ]
    
    for scenario in scenarios:
        print(f"\n🎭 Persona: {scenario['scam_type']}")
        print(f"📩 Scammer says: \"{scenario['message']}\"")
        
        response = requests.post(
            f"{BASE_URL}/honeypot/reply",
            json={
                "scammer_message": scenario['message'],
                "scam_type": scenario['scam_type'],
                "conversation_history": []
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"💬 {result['persona_name']} replies:")
            print(f"   \"{result['reply']}\"")
        else:
            print(f"   ❌ Error: {response.status_code}")

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🛡️ SafeTalk-AI with H.I.V.E. Honeypot - Testing Suite")
    print("="*60)
    
    try:
        # Check if server is running
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print(f"✅ Server is running")
            health = response.json()
            print(f"   Service: {health['service']}")
        else:
            print(f"❌ Server not responding")
            return
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print(f"   Please start the server with: uvicorn backend.main:app --reload --port 8000")
        return
    
    # Run tests
    test_honeypot_detect()
    test_intelligence_extraction()
    test_honeypot_conversation()
    
    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)

if __name__ == "__main__":
    main()
