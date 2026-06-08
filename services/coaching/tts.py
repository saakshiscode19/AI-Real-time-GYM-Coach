from io import BytesIO
from gtts import gTTS
import hashlib
import threading


class TextToSpeech:
    def __init__(self):
        self._cache: dict[str, bytes] = {}
        self._lock = threading.Lock()

    def _clean_text(self, text: str) -> str:
        """Normalize special characters that break gTTS."""
        replacements = {
            "\u2019": "'",   # curly right apostrophe → straight apostrophe
            "\u2018": "'",   # curly left apostrophe
            "\u201c": '"',   # curly left quote
            "\u201d": '"',   # curly right quote
            "\u2014": ", ",  # em dash → comma space
            "\u2013": ", ",  # en dash
            "\u2026": ".",   # ellipsis → period
        }
        for orig, replacement in replacements.items():
            text = text.replace(orig, replacement)
        return text.strip()

    def speak(self, text: str, lang: str = "en") -> bytes | None:
        cleaned = self._clean_text(text or "")
        if not cleaned:
            return None

        cache_key = hashlib.md5(f"{lang}:{cleaned}".encode()).hexdigest()

        with self._lock:
            if cache_key in self._cache:
                return self._cache[cache_key]

        try:
            buffer = BytesIO()
            gTTS(text=cleaned, lang=lang, slow=False).write_to_fp(buffer)
            buffer.seek(0)
            audio_bytes = buffer.read()

            with self._lock:
                self._cache[cache_key] = audio_bytes

            return audio_bytes

        except Exception as e:
            print(f"[TTS ERROR] {e}")
            return None

    def clear_cache(self):
        with self._lock:
            self._cache.clear()