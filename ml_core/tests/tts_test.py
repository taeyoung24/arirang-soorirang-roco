from app.tts_service import TTSService
import httpx, json

API_KEY = "ENTER_API_HERE"

# svc = TTSService(
#     api_key=API_KEY,
#     model="gemini-2.5-flash-preview-tts",
#     voice="Kore",
#     timeout_seconds=30,
# )

# print("Calling TTS API...")
# audio_bytes = svc.synthesize_speech("안녕하세요, 저는 매일 저녁에 일기를 써요.")
# print(f"Got {len(audio_bytes)} bytes of audio")

# with open("tests/test_output.wav", "wb") as f:
#     f.write(audio_bytes)
# print("Saved to tests/test_output.wav")

# print("Testing cache (should be instant)...")
# audio_bytes_2 = svc.synthesize_speech("안녕하세요, 저는 매일 저녁에 일기를 써요.")
# print(f"Cache hit: {audio_bytes is audio_bytes_2}")

response = httpx.post(
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent",
    headers={"x-goog-api-key": "AIzaSyCQ0uo2n37Feu9jG-jIFFk3KBH8FbokpOI", "Content-Type": "application/json"},
    json={
        "contents": [{"parts": [{"text": "Hello, how are you today?"}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Kore"}}},
        },
    },
    timeout=30,
)
print("Status:", response.status_code)
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
