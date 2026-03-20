# ─────────────────────────────────────────────────────────────────
# MaaSakhi Voice Note Handler
# Uses Groq Whisper to transcribe Hindi voice notes
# ─────────────────────────────────────────────────────────────────

import os
import requests
from groq import Groq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")


def transcribe_voice_note(media_url, twilio_sid, twilio_token):
    """
    Downloads voice note from Twilio and transcribes it using Groq Whisper.
    Returns transcribed text or None if failed.
    """
    try:
        # Step 1 — Download audio from Twilio
        response = requests.get(
            media_url,
            auth=(twilio_sid, twilio_token),
            timeout=30
        )

        if response.status_code != 200:
            print(f"Failed to download audio: {response.status_code}")
            return None

        # Step 2 — Save audio temporarily
        audio_path = "/tmp/voice_note.ogg"
        with open(audio_path, "wb") as f:
            f.write(response.content)

        # Step 3 — Transcribe with Groq Whisper
        client = Groq(api_key=GROQ_API_KEY)

        with open(audio_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=audio_file,
                language="hi",
                response_format="text"
            )

        transcribed_text = transcription.strip()
        print(f"Transcribed: {transcribed_text}")
        return transcribed_text

    except Exception as e:
        print(f"Voice transcription error: {e}")
        return None