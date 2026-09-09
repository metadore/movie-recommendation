"""Resolve poster URLs without requiring a TMDB API key (page og:image fallback)."""

from __future__ import annotations

import re
import urllib.request

from tmdb_api import poster_url_for_title, tmdb_configured

UA = {"User-Agent": "Mozilla/5.0 (compatible; CinePulse/1.0)"}

TMDB_PAGES = {
    "inception": "https://www.themoviedb.org/movie/27205-inception",
    "interstellar": "https://www.themoviedb.org/movie/157336-interstellar",
    "the dark knight": "https://www.themoviedb.org/movie/155-the-dark-knight",
    "whiplash": "https://www.themoviedb.org/movie/244786-whiplash",
    "la la land": "https://www.themoviedb.org/movie/313369-la-la-land",
    "mad max: fury road": "https://www.themoviedb.org/movie/76341-mad-max-fury-road",
    "spirited away": "https://www.themoviedb.org/movie/129-spirited-away",
    "the grand budapest hotel": "https://www.themoviedb.org/movie/120467-the-grand-budapest-hotel",
    "arrival": "https://www.themoviedb.org/movie/329865-arrival",
    "parasite": "https://www.themoviedb.org/movie/496243-parasite",
    "john wick": "https://www.themoviedb.org/movie/245891-john-wick",
    "the social network": "https://www.themoviedb.org/movie/37799-the-social-network",
}


def _w500(url: str) -> str:
    match = re.search(r"/t/p/[^/]+(/[^?\s]+)", url)
    if match:
        return f"https://image.tmdb.org/t/p/w500{match.group(1)}"
    return url


def poster_from_tmdb_page(page_url: str) -> str | None:
    try:
        html = urllib.request.urlopen(
            urllib.request.Request(page_url, headers=UA), timeout=20
        ).read().decode("utf-8", "ignore")
    except Exception:
        return None
    match = re.search(r'property="og:image" content="([^"]+)"', html)
    if not match:
        return None
    return _w500(match.group(1))


def resolve_poster(title: str) -> str | None:
    if tmdb_configured():
        try:
            url = poster_url_for_title(title)
            if url:
                return url
        except Exception:
            pass
    page = TMDB_PAGES.get(title.lower().strip())
    if page:
        return poster_from_tmdb_page(page)
    return None
