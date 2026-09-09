# CinePulse — Movie Recommendation App

Full-stack movie recommendation app: FastAPI backend + browser UI.

## Features

- Movie catalog CRUD, search, and genre filter
- User registration / login (JWT)
- Favourites per user
- Recommendations from catalog + favourites (+ Gemini genre hints)
- Gemini mood → genre suggestions
- TMDB details / poster lookup when `TMDB_API_KEY` is set
- Interactive UI at `/`

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Configure `.env`:

```
GEMINI_API_KEY=your_gemini_key
TMDB_API_KEY=your_tmdb_key
JWT_SECRET=change-me
```

TMDB is optional for browsing/recommendations. Get a free key at https://www.themoviedb.org/settings/api

## Seed & run

```bash
python add_movies.py
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

- App: http://127.0.0.1:8000/
- API docs: http://127.0.0.1:8000/docs

## Tests

```bash
python add_movies.py
pytest -q
```
