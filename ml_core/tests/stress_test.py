from app.tts_service import TTSService
from app.stress_analyzer import StressAnalyzer

API_KEY = "ENTER_API_HERE"
SCRIPT = "저는 매일 저녁에 일기를 써요"

# Get TTS reference audio
tts = TTSService(
    api_key=API_KEY,
    model="gemini-2.5-flash-preview-tts",
    voice="Kore",
    timeout_seconds=30,
)
ref_audio = tts.synthesize_speech(SCRIPT)
print(f"TTS audio: {len(ref_audio)} bytes")

# Run stress analysis (using TTS as both user and reference for now)
# In real usage, user_audio comes from the uploaded WAV
analyzer = StressAnalyzer()
results = analyzer.analyze(
    user_audio_bytes=ref_audio,  # using TTS as fake user audio
    ref_audio_bytes=ref_audio,
    script=SCRIPT,
)

print(f"\nFound {len(results)} syllables:\n")
for r in results:
    status = "MISMATCH" if r.is_mismatch else "ok"
    print(
        f"  [{r.index}] {r.syllable} | "
        f"user_f0={r.user_f0} ref_f0={r.ref_f0} | "
        f"user_energy={r.user_energy} ref_energy={r.ref_energy} | "
        f"stressed_ref={r.is_stressed_ref} stressed_user={r.is_stressed_user} | "
        f"{status}"
    )
