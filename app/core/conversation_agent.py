"""
H.I.V.E. Conversation Agent
Gemini-powered conversation agent with persona — no fallbacks
"""
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
from app.core.persona_manager import get_persona_system_prompt

load_dotenv()

# Models to try in order (some may be quota-limited on free tier)
GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash-lite",
]


def generate_reply(persona: dict, scammer_message: str, conversation_history: list = None) -> str:
    """
    Generate a reply as the persona to the scammer's message using Gemini AI.
    Raises on failure — no fallback responses.
    """

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise RuntimeError("GEMINI_API_KEY is not set. Add it to your .env file.")

    client = genai.Client(api_key=api_key)

    # Build system + user prompts
    system_prompt = get_persona_system_prompt(persona)

    history_text = ""
    if conversation_history:
        recent = conversation_history[-6:]
        history_text = "\n".join(
            f"Scammer: {msg['text']}" if msg.get("sender") == "scammer" else f"You: {msg['text']}"
            for msg in recent
        )

    user_prompt = f"""
{'RECENT CONVERSATION:\n' + history_text if history_text else 'This is the first message.'}

SCAMMER JUST SAID: "{scammer_message}"

Write your reply as the victim character. Remember:
- Maximum 2-3 sentences only
- Sound emotional and human, not robotic
- Follow your character's speech style
- Try to extract scammer's contact details
- Stay completely in character
- Do NOT reveal you are AI"""

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=0.9,
    )

    # Try each model until one succeeds
    last_error = None
    for model_name in GEMINI_MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=user_prompt,
                config=config,
            )
            reply = response.text.strip()
            # Strip surrounding quotes if present
            if reply.startswith('"') and reply.endswith('"'):
                reply = reply[1:-1]
            return reply
        except Exception as e:
            last_error = e
            print(f"⚠️  Model {model_name} failed: {e}")
            continue

    # All models exhausted — propagate error instead of falling back
    raise RuntimeError(f"All Gemini models failed. Last error: {last_error}")
