import os

import requests
from dotenv import load_dotenv

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"


def _api_key() -> str | None:
    if not TMDB_API_KEY or TMDB_API_KEY.startswith("your_actual_"):
        return None
    return TMDB_API_KEY


def tmdb_configured() -> bool:
    return _api_key() is not None


def fetch_movie_details_tmdb(movie_id: int) -> dict:
    key = _api_key()
    if not key:
        raise Exception("TMDB_API_KEY not found in environment variables")

    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={key}"
    response = requests.get(url, timeout=30)
    if response.status_code != 200:
        raise Exception(f"TMDB API error: {response.text}")
    return response.json()


def search_movie_tmdb(title: str) -> dict | None:
    key = _api_key()
    if not key:
        return None

    response = requests.get(
        "https://api.themoviedb.org/3/search/movie",
        params={"api_key": key, "query": title},
        timeout=30,
    )
    if response.status_code != 200:
        raise Exception(f"TMDB API error: {response.text}")
    results = response.json().get("results") or []
    return results[0] if results else None


def poster_url_for_title(title: str) -> str | None:
    hit = search_movie_tmdb(title)
    if not hit or not hit.get("poster_path"):
        return None
    return f"{TMDB_IMAGE_BASE}{hit['poster_path']}"
