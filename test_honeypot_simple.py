"""
Test SafeTalk-AI with AI Honeypot Integration
Simple workflow: Detect scam → Engage with AI → Extract intelligence
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def print_header(text):
    print("\n" + "="*60)
    print(text)
    print("="*60)

def test_simple_workflow():
    """Test the complete workflow"""
    print_header("SafeTalk-AI + AI Honeypot - Complete Workflow Test")
    
    # Step 1: Detect scam using SafeTalk-AI
    print("\n🔍 STEP 1: Detect Scam (SafeTalk-AI ML Model)")
    scam_message = "Your bank account will be blocked today. Send OTP immediately to verify."
    
    response = requests.post(
        f"{BASE_URL}/analyze-text",
        json={"message": scam_message}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"📩 Message: \"{scam_message}\"")
        print(f"⚠️  Risk: {result['risk']}")
        print(f"📊 Confidence: {result['confidence']}")
        print(f"💬 Reason: {result['reason']}")
        
        is_scam = "scam" in result['risk'].lower()
        
        if is_scam:
            print("\n✅ Scam detected! Activating AI honeypot mode...")
            
            # Step 2: Engage with AI Honeypot
            print("\n🤖 STEP 2: Generate AI Honeypot Reply")
            
            honeypot_response = requests.post(
                f"{BASE_URL}/honeypot/reply",
                json={
                    "scammer_message": scam_message,
                    "scam_type": "bank_fraud",
                    "conversation_history": []
                }
            )
            
            if honeypot_response.status_code == 200:
                honeypot = honeypot_response.json()
                print(f"🎭 Persona: {honeypot['persona_name']}")
                print(f"💬 AI Reply: \"{honeypot['reply']}\"")
            else:
                print(f"❌ Honeypot error: {honeypot_response.status_code}")
                print(f"   {honeypot_response.text}")
            
            # Step 3: Extract intelligence
            print("\n📊 STEP 3: Extract Intelligence")
            
            intel_response = requests.post(
                f"{BASE_URL}/honeypot/extract",
                json={"message": scam_message}
            )
            
            if intel_response.status_code == 200:
                intel = intel_response.json()
                print(f"💳 UPI IDs: {intel['upiIds'] if intel['upiIds'] else 'None found'}")
                print(f"📞 Phone Numbers: {intel['phoneNumbers'] if intel['phoneNumbers'] else 'None found'}")
                print(f"🔗 Links: {intel['phishingLinks'] if intel['phishingLinks'] else 'None found'}")
                print(f"⚠️  Suspicious Keywords: {', '.join(intel['suspiciousKeywords'][:5])}")
        else:
            print("\n✅ Message appears legitimate. No honeypot activation needed.")
    else:
        print(f"❌ Error: {response.status_code}")

def test_conversation_flow():
    """Test a multi-turn conversation"""
    print_header("Multi-Turn Honeypot Conversation")
    
    conversation = [
        "Your bank account has been compromised. Verify immediately.",
        "Send Rs.10 to verify@okhdfc to unlock your account.",
        "Why are you taking time? Call 9876543210 now!"
    ]
    
    conversation_history = []
    
    for i, scammer_msg in enumerate(conversation, 1):
        print(f"\n🔄 Turn {i}")
        print(f"😈 Scammer: \"{scammer_msg}\"")
        
        # Generate AI reply
        response = requests.post(
            f"{BASE_URL}/honeypot/reply",
            json={
                "scammer_message": scammer_msg,
                "scam_type": "bank_fraud",
                "conversation_history": conversation_history
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"🎭 {result['persona_name']}: \"{result['reply']}\"")
            
            # Add to history
            conversation_history.append({
                "sender": "scammer",
                "text": scammer_msg
            })
            conversation_history.append({
                "sender": "victim",
                "text": result['reply']
            })
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   {response.text}")
            break
    
    # Extract all intelligence from conversation
    print("\n📊 Intelligence Extracted from Entire Conversation:")
    full_conversation = " ".join(conversation)
    
    intel_response = requests.post(
        f"{BASE_URL}/honeypot/extract",
        json={"message": full_conversation}
    )
    
    if intel_response.status_code == 200:
        intel = intel_response.json()
        print(f"💳 UPI IDs: {intel['upiIds']}")
        print(f"📞 Phone Numbers: {intel['phoneNumbers']}")
        print(f"🔗 Phishing Links: {intel['phishingLinks']}")

def main():
    """Run all tests"""
    try:
        # Check if server is running
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            health = response.json()
            print(f"✅ {health['service']} is online")
            print(f"   Scam Detection: {health['features']['scam_detection']}")
            print(f"   AI Conversation: {health['features']['ai_conversation']}")
        else:
            print(f"❌ Server not responding properly")
            return
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print(f"   Start server: python -m uvicorn backend.main:app --reload --port 8000")
        return
    
    # Run tests
    test_simple_workflow()
    test_conversation_flow()
    
    print("\n" + "="*60)
    print("✅ Testing Complete!")
    print("="*60)
    print("\n📝 How it works:")
    print("   1. SafeTalk-AI ML model detects scams")
    print("   2. AI honeypot engages scammer with realistic personas")
    print("   3. Intelligence extractor captures scammer details")
    print("   4. System wastes scammer's time while gathering evidence")

if __name__ == "__main__":
    main()
