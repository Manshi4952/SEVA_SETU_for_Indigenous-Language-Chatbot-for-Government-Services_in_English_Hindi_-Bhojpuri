"""
api/routes/voice.py – TTS and STT endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
import tempfile, os

from app.core.deps import get_current_user
from app.core.config import settings
from app.models.orm import User

router = APIRouter(prefix="/voice", tags=["voice"])


class TTSRequest(BaseModel):
    text: str
    language: str = "hindi"


@router.post("/tts")
def text_to_speech_endpoint(
    req: TTSRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        from app.services.voice_service import text_to_speech
        url = text_to_speech(req.text, req.language, settings.AUDIO_OUTPUT_DIR)
        return {"audio_url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {e}")


@router.post("/stt")
async def speech_to_text_endpoint(
    language: str = "hindi",
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    try:
        from app.services.voice_service import speech_to_text
        suffix = os.path.splitext(audio.filename)[1] or ".wav"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await audio.read())
            tmp_path = tmp.name
            
        # Send the temp file to the converter (which now handles .webm)
        text = speech_to_text(tmp_path, language)
        os.unlink(tmp_path)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT error: {e}")

    # ==========================================
    # NEW LOGIC: Catch empty transcriptions
    # ==========================================
    # We do this OUTSIDE the try/except block so it correctly sends a 422 status
    if not text:
        raise HTTPException(
            status_code=422, 
            detail="Could not understand audio. Please speak clearly for 8 seconds."
        )

    return {"text": text}