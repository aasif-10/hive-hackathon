import sys
sys.stdout.reconfigure(encoding='utf-8')
audio_file = sys.argv[1]
import os
import whisper
import ffmpeg as ff
import requests

if len(sys.argv) < 2:
    print("❌ Audio file path not provided.")
    exit(1)

input_path = os.path.abspath(sys.argv[1])
if not os.path.exists(input_path):
    print(f"❌ File not found: {input_path}")
    exit(1)

TEMP_MP3 = "temp.mp3"

print(f"\n📂 File detected: {os.path.basename(input_path)}")
print(f"📍 Absolute path: {input_path}")
print("🔄 Converting to MP3 via ffmpeg-python...")

try:
    (
        ff
        .input(input_path)
        .output(TEMP_MP3, format='mp3')
        .run(overwrite_output=True, quiet=True)
    )
    print("✅ Conversion completed.")
except Exception as e:
    print(f"❌ Error during conversion with ffmpeg-python:\n{e}")
    exit(1)

print("🎙️ Starting transcription with Whisper...")
try:
    model = whisper.load_model("small")
    result = model.transcribe(TEMP_MP3, language='pt')
    transcribed_text = result['text']
    print("📄 Transcription:")
    print(transcribed_text)

    print("📡 Sending transcription for analysis...")
    response = requests.post("http://localhost:8000/analyze-text", json={"message": transcribed_text})
    if response.status_code == 200:
        analysis = response.json()
        print("\n🧠 AI Result:")
        print(f"🔍 Risk: {analysis['risk']}")
        print(f"💬 Reason: {analysis['reason']}")
        print(f"📊 Confidence: {analysis['confidence']}")
    else:
        print(f"⚠️ Error analyzing transcription. Status: {response.status_code}")
except Exception as e:
    print(f"❌ Error in transcription or analysis:\n{e}")

# 🧹 Clean up temporary file
if os.path.exists(TEMP_MP3):
    os.remove(TEMP_MP3)
