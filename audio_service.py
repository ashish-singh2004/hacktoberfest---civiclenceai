"""
CivicLens AI - Voice Accessibility Service
Generates audio briefings for visually impaired pedestrians and citizen advocates
using Google Text-to-Speech (gTTS).

Supports bilingual speech generation (English and Hindi) with in-memory caching.
"""

import io
import os
import hashlib
from typing import Optional


def generate_audio_briefing(text: str, lang: str = "en") -> Optional[bytes]:
    """
    Converts a concise hazard summary into spoken audio bytes (MP3).
    
    Args:
        text: Short, clear text to speak.
        lang: Language code ('en' for English, 'hi' for Hindi).
        
    Returns:
        Audio bytes in MP3 format, or None if gTTS fails.
    """
    if not text or not text.strip():
        return None

    try:
        from gtts import gTTS
        tts_lang = "hi" if lang == "hi" else "en"
        tts = gTTS(text=text.strip(), lang=tts_lang, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except Exception as e:
        # Graceful fallback if offline
        return None


def build_spoken_summary(issue_title: str, impact: str, lang: str = "en") -> str:
    """Builds a friendly, conversational audio warning message."""
    if lang == "hi":
        return f"सुगमता सूचना। {issue_title}। {impact}। कृपया सावधानी बरतें।"
    return f"Accessibility alert. {issue_title}. {impact}. Please proceed with caution."
