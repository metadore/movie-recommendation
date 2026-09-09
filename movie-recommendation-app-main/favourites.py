from fastapi import APIRouter, Depends, HTTPException

from auth import get_current_user
from database import database
from models import favourites_table, movies_table

router = APIRouter(prefix="/api/favourites", tags=["favourites"])


@router.get("")
async def list_favourites(user=Depends(get_current_user)):
    query = (
        movies_table.select()
        .select_from(
            favourites_table.join(
                movies_table, favourites_table.c.movie_id == movies_table.c.id
            )
        )
        .where(favourites_table.c.user_id == user["id"])
    )
    rows = await database.fetch_all(query)
    return [dict(r) for r in rows]


@router.post("/{movie_id}")
async def add_favourite(movie_id: int, user=Depends(get_current_user)):
    movie = await database.fetch_one(
        movies_table.select().where(movies_table.c.id == movie_id)
    )
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    existing = await database.fetch_one(
        favourites_table.select().where(
            (favourites_table.c.user_id == user["id"])
            & (favourites_table.c.movie_id == movie_id)
        )
    )
    if existing:
        return {"message": "Already in favourites", "movie_id": movie_id}

    await database.execute(
        favourites_table.insert().values(user_id=user["id"], movie_id=movie_id)
    )
    return {"message": "Added to favourites", "movie_id": movie_id}


@router.delete("/{movie_id}")
async def remove_favourite(movie_id: int, user=Depends(get_current_user)):
    result = await database.execute(
        favourites_table.delete().where(
            (favourites_table.c.user_id == user["id"])
            & (favourites_table.c.movie_id == movie_id)
        )
    )
    if not result:
        raise HTTPException(status_code=404, detail="Favourite not found")
    return {"message": "Removed from favourites", "movie_id": movie_id}
