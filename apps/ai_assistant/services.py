import os
from groq import Groq
from .prompts import SYSTEM_PROMPT

class AIServiceError(Exception):
    pass

def generate_ai_reply(user_message, history=None):
    api_key = os.getenv("GROQ_API_KEY", "").strip()

    if not api_key:
        raise AIServiceError("GROQ_API_KEY is missing from the .env file.")

    client = Groq(api_key=api_key)

    try:
        conversation_history = []
        for item in (history or [])[-10:]:
            if not isinstance(item, dict):
                continue
            role = item.get("role")
            content = str(item.get("content", "")).strip()
            if role in {"user", "assistant"} and content:
                conversation_history.append(
                    {"role": role, "content": content[:4000]}
                )

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                *conversation_history,
                {"role": "user", "content": user_message},
            ],
            temperature=0.5,
            max_tokens=500,
        )
    except Exception as exc:
        raise AIServiceError("The AI service could not generate a reply.") from exc

    return response.choices[0].message.content
