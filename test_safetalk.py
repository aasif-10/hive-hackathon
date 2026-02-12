"""
Test script for SafeTalk-AI scam detection API
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_scam_detection():
    """Test the scam detection endpoint"""
    print("="*60)
    print("TESTING SAFETALK-AI SCAM DETECTION")
    print("="*60)
    
    test_cases = [
        {
            "name": "Scam Message - Bank Fraud",
            "message": "Your bank account will be blocked today. Verify immediately by sending OTP.",
            "expected": "scam"
        },
        {
            "name": "Scam Message - UPI Fraud",
            "message": "Urgent! Send Rs.10 to verify@okhdfc to avoid account suspension.",
            "expected": "scam"
        },
        {
            "name": "Scam Message - Phishing",
            "message": "Your KYC is incomplete. Download this app and enter your PIN to update.",
            "expected": "scam"
        },
        {
            "name": "Legitimate Message - Greeting",
            "message": "Hi, how are you doing today?",
            "expected": "legitimate"
        },
        {
            "name": "Legitimate Message - Meeting",
            "message": "Can we reschedule our meeting to tomorrow at 3pm?",
            "expected": "legitimate"
        },
        {
            "name": "Scam Message - Legal Threat",
            "message": "Police case filed against you. Pay fine Rs.10000 immediately or face arrest.",
            "expected": "scam"
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test['name']}")
        print(f"   Message: \"{test['message'][:50]}...\"" if len(test['message']) > 50 else f"   Message: \"{test['message']}\"")
        
        try:
            response = requests.post(
                f"{BASE_URL}/analyze-text",
                json={"message": test["message"]},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✓ Status: {response.status_code}")
                print(f"   📊 Result:")
                print(f"      - Risk Level: {result.get('risk', 'N/A')}")
                print(f"      - Confidence: {result.get('confidence', 0):.2f}")
                print(f"      - Reason: {result.get('reason', 'N/A')[:60]}...")
                
                # Check if prediction matches expected
                risk = result.get('risk', '').lower()
                if test['expected'] in risk or (test['expected'] == 'scam' and 'scam' in risk):
                    print(f"   ✅ PASS - Correctly identified as {test['expected']}")
                    passed += 1
                else:
                    print(f"   ❌ FAIL - Expected {test['expected']}, got {risk}")
                    failed += 1
            else:
                print(f"   ❌ FAIL - HTTP {response.status_code}: {response.text}")
                failed += 1
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ FAIL - Cannot connect to server at {BASE_URL}")
            print(f"   💡 Make sure the server is running with: uvicorn backend.main:app --reload --port 8000")
            failed += 1
        except Exception as e:
            print(f"   ❌ FAIL - Error: {str(e)}")
            failed += 1
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"✅ Passed: {passed}/{len(test_cases)}")
    print(f"❌ Failed: {failed}/{len(test_cases)}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! SafeTalk-AI is working correctly!")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the results above.")
    
    print("="*60)
    return passed, failed

if __name__ == "__main__":
    test_scam_detection()
