from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func

from auth import get_current_user, require_role
from database import database
from models import movies_table
from posters import resolve_poster
from schemas import MovieCreate, MovieOut

router = APIRouter(prefix="/api/movies", tags=["movies"])


@router.get("", response_model=list[MovieOut])
async def get_movies():
    rows = await database.fetch_all(movies_table.select())
    return [dict(r) for r in rows]


@router.post("", response_model=MovieOut)
async def add_movie(
    movie: MovieCreate,
    _user=Depends(require_role("admin")),  # only admins can add movies
):
    payload = movie.model_dump()
    if not payload.get("image"):
        payload["image"] = resolve_poster(movie.title)
    movie_id = await database.execute(movies_table.insert().values(**payload))
    return {**payload, "id": movie_id}


@router.put("/{movie_id}")
async def update_movie(
    movie_id: int,
    movie: MovieCreate,
    _user=Depends(require_role("admin")),  # only admins can update movies
):
    existing = await database.fetch_one(
        movies_table.select().where(movies_table.c.id == movie_id)
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Movie not found")
    await database.execute(
        movies_table.update()
        .where(movies_table.c.id == movie_id)
        .values(**movie.model_dump())
    )
    return {"message": "Movie updated successfully"}


@router.delete("/{movie_id}")
async def delete_movie(
    movie_id: int,
    _user=Depends(require_role("admin")),  # only admins can delete movies
):
    from models import favourites_table

    existing = await database.fetch_one(
        movies_table.select().where(movies_table.c.id == movie_id)
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Movie not found")
    await database.execute(
        favourites_table.delete().where(favourites_table.c.movie_id == movie_id)
    )
    await database.execute(
        movies_table.delete().where(movies_table.c.id == movie_id)
    )
    return {"message": "Movie deleted successfully"}


@router.get("/search")
async def search_movies(title: str):
    rows = await database.fetch_all(
        movies_table.select().where(
            func.lower(movies_table.c.title).like(f"%{title.lower()}%")
        )
    )
    return [dict(r) for r in rows]


@router.get("/filter")
async def filter_movies(genre: str):
    rows = await database.fetch_all(
        movies_table.select().where(
            func.lower(movies_table.c.genre).like(f"%{genre.lower()}%")
        )
    )
    return [dict(r) for r in rows]
