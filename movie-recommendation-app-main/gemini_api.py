import os
import re

import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-3.6-flash"


def _api_key() -> str:
    if not GEMINI_API_KEY or GEMINI_API_KEY.startswith("your_actual_"):
        raise Exception("GEMINI_API_KEY not found in environment variables")
    return GEMINI_API_KEY


def _generate(prompt: str) -> str:
    key = _api_key()
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={key}"
    )
    response = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=45,
    )
    if response.status_code != 200:
        raise Exception(f"Gemini API error: {response.text}")
    data = response.json()
    parts = data["candidates"][0]["content"]["parts"]
    texts = [p.get("text", "") for p in parts if p.get("text")]
    return "\n".join(texts).strip()


def fetch_movies_from_gemini(mood: str = "happy") -> dict:
    """Return raw Gemini payload plus parsed genre list."""
    text = _generate(
        f"Suggest 3 movie genres for someone feeling {mood}. "
        "Return only a comma-separated list of genre names."
    )
    genres = [g.strip() for g in re.split(r"[,\n]+", text) if g.strip()]
    return {"mood": mood, "text": text, "genres": genres[:5]}


def suggest_related_genres(title: str, genre: str | None = None) -> list[str]:
    hint = f" Genre hint: {genre}." if genre else ""
    try:
        text = _generate(
            f'Someone liked the movie "{title}".{hint} '
            "Suggest 4 related movie genres as a comma-separated list only."
        )
        return [g.strip() for g in re.split(r"[,\n]+", text) if g.strip()][:4]
    except Exception:
        return []
