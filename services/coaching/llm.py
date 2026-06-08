from services.config.workout_config import PROMPT

class LLMCoach:
    def __init__(self, groq_client):
        self.client = groq_client
        self.history = []
        self.system_prompt = PROMPT

    def give_feedback(self, event, issue):
        prompt = f"Event: {event}"
        if issue:
            prompt += f". Form Issue: {issue}"

        messages = [
            {"role": "system", "content": self.system_prompt},
            *self.history[-6:],
            {"role": "user", "content": prompt}
        ]

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.4,
            max_tokens=50,
        )

        text = response.choices[0].message.content.strip()
        print(f"[LLM RAW]: '{text}'")         # ← debug line
        text = self._ensure_complete_sentence(text)
        print(f"[LLM TRIMMED]: '{text}'")     # ← debug line

        self.history.append({"role": "assistant", "content": text})
        return text

    def _ensure_complete_sentence(self, text: str) -> str:
        if not text:
            return ""
        for punct in ["!", ".", "?"]:
            idx = text.find(punct)
            if 10 <= idx <= 120:
                return text[:idx + 1].strip()
        trimmed = text[:100].rsplit(" ", 1)[0]
        return trimmed.rstrip(",;:") + "."