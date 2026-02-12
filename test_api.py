from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key =os.getenv("GEMINI_API_KEY")
print(f"API Key loaded: {api_key[:20]}...")

try:
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model='gemini-2.0-flash-exp',
        contents='Say hello in one sentence'
    )
    print(f"✅ API Working! Response: {response.text}")
except Exception as e:
    print(f"❌ API Error: {e}")
