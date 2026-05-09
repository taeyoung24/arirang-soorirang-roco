from __future__ import annotations
import base64
import hashlib
import httpx
import wave
import io

class TTSService:
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, api_key: str, model: str, voice: str, timeout_seconds: float):
        self.api_key = api_key.strip()
        self.model = model
        self.voice = voice
        self.timeout_seconds = timeout_seconds
        # self._cache is a dic with keys are str and values are bytes
        self._cache: dict[str, bytes] = {}
    

    @property
    def has_api_key(self) -> bool:
        return bool(self.api_key)
    
    @staticmethod
    def _pcm_to_wav(pcm_bytes: bytes, sample_rate: int = 24000) -> bytes:
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm_bytes)
        return buffer.getvalue()
    
    def synthesize_speech(self, script: str) -> bytes:
        """
        Generate speech audio from input text

        The generated audio is cached using a hash key
        based on the model, voice and script context.
        """

        # Create a unique identifier for the TTS request.
        cache_key = hashlib.md5(f"{self.model}:{self.voice}:{script}".encode()).hexdigest()

        if cache_key in self._cache:
            return self._cache[cache_key]

        audio_bytes = self._fetch_tts_audio(script)
        self._cache[cache_key] = audio_bytes
        return audio_bytes
    
    def _fetch_tts_audio(self, script: str) -> bytes:
        """
        Sends text to the API and retrieves synthesized speech

        Returns:
            The raw binary audio data decoded from Base64
        """

        if not self.has_api_key:
            raise RuntimeError("TTS API key is not configured!")
        
        payload = {
            "contents": [{"parts": [{"text": script}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {"voiceName": self.voice}
                    }
                },
            },
        }

        url = f"{self.BASE_URL}/{self.model}:generateContent"

        headers = {
            'x-goog-api-key': self.api_key,
            "Content-Type": "application/json"
        }

        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()

        parsed_response = response.json()
        
        try: 
            base64_audio = parsed_response["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]

        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Unexpected TTS response shape: {parsed_response}") from exc

        pcm_bytes = base64.b64decode(base64_audio)
        return self._pcm_to_wav(pcm_bytes, sample_rate=24000)



        
        

    

