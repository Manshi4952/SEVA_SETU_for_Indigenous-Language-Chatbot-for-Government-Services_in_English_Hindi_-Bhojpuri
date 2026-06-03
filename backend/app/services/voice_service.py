"""
services/voice_service.py  –  Text-to-Speech and Speech-to-Text helpers.

TTS: gTTS (Google Text-to-Speech) with Hindi/Bhojpuri support.
STT: SpeechRecognition with Google backend.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Optional


LANG_MAP = {
    "english":  "en",
    "hindi":    "hi",
    "bhojpuri": "hi",   # Bhojpuri uses Hindi TTS as closest match
}


def text_to_speech(text: str, language: str = "hindi", output_dir: str = "./static/audio") -> str:
    """
    Convert text to MP3 using gTTS.
    Returns the relative URL path to the audio file.
    """
    from gtts import gTTS

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    lang_code = LANG_MAP.get(language, "hi")
    # Deterministic filename so identical queries reuse cached audio
    hash_key = hashlib.md5(f"{text}{lang_code}".encode()).hexdigest()[:12]
    filename = f"tts_{hash_key}.mp3"
    filepath = Path(output_dir) / filename

    if not filepath.exists():
        tts = gTTS(text=text, lang=lang_code, slow=False)
        tts.save(str(filepath))

    return f"/static/audio/{filename}"


def estimate_duration(text: str) -> float:
    """Rough TTS duration in seconds (avg 150 words/min)."""
    words = len(text.split())
    return round(words / 2.5, 1)   # ~150 wpm = 2.5 words/sec




def speech_to_text(audio_file_path: str, language: str = "hindi") -> Optional[str]:
    from pydub import AudioSegment
    import speech_recognition as sr
    import os
    
    wav_path = audio_file_path
    
    # 1. Convert WebM to WAV dynamically
    if audio_file_path.endswith(".webm"):
        wav_path = audio_file_path + ".wav"
        try:
            AudioSegment.from_file(audio_file_path).export(wav_path, format="wav")
        except Exception as e:
            print(f"[Voice] FFmpeg conversion error: {e}")
            return None

    # 2. Map the language codes (Bhojpuri routes to Hindi STT)
    lang_code = {"english": "en-IN", "hindi": "hi-IN", "bhojpuri": "hi-IN"}.get(language, "hi-IN")
    
    # 3. Transcribe the audio
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
        
        text = recognizer.recognize_google(audio_data, language=lang_code)
        
        # Cleanup temporary files (Optional but highly recommended)
        if os.path.exists(wav_path) and wav_path != audio_file_path:
            os.remove(wav_path)
            
        return text
    except sr.UnknownValueError:
        return None  # Could not understand audio
    except sr.RequestError as e:
        print(f"[Voice] API unavailable: {e}")
        return None
