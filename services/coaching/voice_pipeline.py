import time
import threading
import io
import base64
import streamlit as st


class VoicePipeline:
    def __init__(self, llm, tts):
        self.llm = llm
        self.tts = tts
        self.last_spoken_at = 0
        self._lock = threading.Lock()  # prevent race conditions

    def _find_form_issue(self, exercise, metrics):
        if "issue" in metrics:
            return metrics["issue"]

        if exercise == "Squats":
            depth = metrics.get("depth_status", "")
            back_angle = metrics.get("back_angle", 180)
            if depth == "TOO HIGH":
                return "The user's squat is not deep enough — knees are not bending sufficiently."
            if isinstance(back_angle, (int, float)) and back_angle < 130:
                return "The user is leaning too far forward during the squat."

        elif exercise == "Push-ups":
            alignment = metrics.get("body_alignment", "")
            hip_status = metrics.get("hip_status", "")
            if alignment == "Poor Form":
                return "The user's body is not straight during the push-up."
            if hip_status == "SAGGING":
                return "The user's hips are sagging down during the push-up."
            if hip_status == "PIKED UP":
                return "The user's hips are too high — lower them to form a straight line."

        elif exercise == "Biceps Curls (Dumbbell)":
            swing = metrics.get("swing_status", "")
            shoulder = metrics.get("shoulder_status", "")
            if swing == "SWINGING":
                return "The user is swinging their torso during the curl — keep the body still."
            if shoulder == "ELBOW DRIFTING":
                return "The user's elbow is drifting away from their side during the curl."

        elif exercise == "Shoulder Press":
            back_arch = metrics.get("back_arch_status", "")
            extension = metrics.get("extension_status", "")
            if back_arch == "Excessive Arch":
                return "The user is arching their lower back excessively during the press."
            if back_arch == "Slight Arch":
                return "Slight back arch detected — encourage the user to brace their core."

        elif exercise == "Lunges":
            balance = metrics.get("balance_status", "")
            if balance == "OFF BALANCE":
                return "The user is losing balance during the lunge — feet should be hip-width apart."

        return None

    def process_event(self, event, exercise, metrics):
        issue = self._find_form_issue(exercise, metrics)
        now = time.time()

        is_major_event = event in ["workout_started", "set_completed", "workout_completed"]

        # For minor events: skip if no issue or cooldown hasn't elapsed
        if not is_major_event:
            if not issue:
                return None
            if now - self.last_spoken_at < 5:
                return None

        # Generate feedback text from LLM
        text = self.llm.give_feedback(event, issue)
        if not text:
            return None

        # Generate audio bytes from TTS
        audio_bytes = self.tts.speak(text)
        if not audio_bytes:
            return None

        # Update cooldown timestamp (thread-safe)
        with self._lock:
            self.last_spoken_at = now

        # Return ONLY audio_bytes so autoplay_audio() gets the right type
        return audio_bytes, text


def autoplay_audio(audio_bytes: bytes):
    """
    Reliably autoplays audio in Streamlit using a base64-encoded HTML audio tag.
    Works across browsers without needing a user gesture for short clips.
    """
    if not audio_bytes:
        return

    b64 = base64.b64encode(audio_bytes).decode("utf-8")
    audio_html = f"""
        <audio autoplay="true" style="display:none;">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)