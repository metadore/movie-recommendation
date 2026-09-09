from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from auth import (
    create_access_token,
    get_current_user,
    get_optional_user,
    hash_password,
    verify_password,
)
from contextlib import asynccontextmanager
from database import database
from gemini_api import fetch_movies_from_gemini
from models import ensure_schema, users_table
import favourites as favourites_router
import movies as movies_router
from recommend import recommend_movies
from schemas import TokenOut, UserCreate, UserLogin, UserOut
from tmdb_api import fetch_movie_details_tmdb, tmdb_configured

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_schema()
    await database.connect()
    yield
    await database.disconnect()


app = FastAPI(title="CinePulse", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(movies_router.router)
app.include_router(favourites_router.router)


@app.get("/api/health")
async def health():
    return {
        "message": "Backend running",
        "tmdb_configured": tmdb_configured(),
    }


@app.post("/api/auth/register", response_model=TokenOut)
async def register(payload: UserCreate):
    existing = await database.fetch_one(
        users_table.select().where(users_table.c.username == payload.username)
    )
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")
    user_id = await database.execute(
        users_table.insert().values(
            username=payload.username,
            password_hash=hash_password(payload.password),
        )
    )
    token = create_access_token(user_id, payload.username)
    return TokenOut(access_token=token, username=payload.username)


@app.post("/api/auth/login", response_model=TokenOut)
async def login(payload: UserLogin):
    user = await database.fetch_one(
        users_table.select().where(users_table.c.username == payload.username)
    )
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token(user["id"], user["username"])
    return TokenOut(access_token=token, username=user["username"])


@app.get("/api/auth/me", response_model=UserOut)
async def me(user=Depends(get_current_user)):
    return UserOut(id=user["id"], username=user["username"])


@app.get("/api/gemini/movies")
async def gemini_movies(mood: str = Query("happy")):
    try:
        return fetch_movies_from_gemini(mood=mood)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch from Gemini API: {str(e)}"
        )


@app.get("/api/tmdb/movie/{movie_id}")
async def tmdb_movie_details(movie_id: int):
    try:
        return {"details": fetch_movie_details_tmdb(movie_id)}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch from TMDB API: {str(e)}"
        )


@app.get("/api/recommend")
async def recommend(
    movie: str = Query(..., min_length=1),
    user=Depends(get_optional_user),
):
    user_id = user["id"] if user else None
    return await recommend_movies(seed=movie, user_id=user_id)


# Legacy aliases so older clients keep working
@app.get("/movies")
async def legacy_movies():
    from models import movies_table

    rows = await database.fetch_all(movies_table.select())
    return [dict(r) for r in rows]


@app.get("/recommend")
async def legacy_recommend(movie: str, user=Depends(get_optional_user)):
    user_id = user["id"] if user else None
    return await recommend_movies(seed=movie, user_id=user_id)


@app.get("/gemini/movies")
async def legacy_gemini():
    try:
        return {"movies": fetch_movies_from_gemini()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def frontend_index():
    index = STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"message": "Backend running", "docs": "/docs"}
