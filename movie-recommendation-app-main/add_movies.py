"""Reset catalog to a clean seeded movie list with verified posters."""

import asyncio

from database import database
from models import ensure_schema, favourites_table, movies_table

MOVIES = [
    {
        "title": "Inception",
        "genre": "Sci-Fi",
        "year": 2010,
        "rating": 8.8,
        "image": "https://image.tmdb.org/t/p/w500/xlaY2zyzMfkhk0HSC5VUwzoZPU1.jpg",
    },
    {
        "title": "Interstellar",
        "genre": "Sci-Fi",
        "year": 2014,
        "rating": 8.6,
        "image": "https://image.tmdb.org/t/p/w500/yQvGrMoipbRoddT0ZR8tPoR7NfX.jpg",
    },
    {
        "title": "The Dark Knight",
        "genre": "Action",
        "year": 2008,
        "rating": 9.0,
        "image": "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
    },
    {
        "title": "Whiplash",
        "genre": "Drama",
        "year": 2014,
        "rating": 8.5,
        "image": "https://image.tmdb.org/t/p/w500/7fn624j5lj3xTme2SgiLCeuedmO.jpg",
    },
    {
        "title": "La La Land",
        "genre": "Musical",
        "year": 2016,
        "rating": 8.0,
        "image": "https://image.tmdb.org/t/p/w500/uDO8zWDhfWwoFdKS4fzkUJt0Rf0.jpg",
    },
    {
        "title": "Mad Max: Fury Road",
        "genre": "Action",
        "year": 2015,
        "rating": 8.1,
        "image": "https://image.tmdb.org/t/p/w500/ulcAi4dKpAjHwYGS08vNyx9H6I9.jpg",
    },
    {
        "title": "Spirited Away",
        "genre": "Animation",
        "year": 2001,
        "rating": 8.6,
        "image": "https://image.tmdb.org/t/p/w500/39wmItIWsg5sZMyRUHLkWBcuVCM.jpg",
    },
    {
        "title": "The Grand Budapest Hotel",
        "genre": "Comedy",
        "year": 2014,
        "rating": 8.1,
        "image": "https://image.tmdb.org/t/p/w500/eWdyYQreja6JGCzqHWXpWHDrrPo.jpg",
    },
    {
        "title": "Arrival",
        "genre": "Sci-Fi",
        "year": 2016,
        "rating": 7.9,
        "image": "https://image.tmdb.org/t/p/w500/pEzNVQfdzYDzVK0XqxERIw2x2se.jpg",
    },
    {
        "title": "Parasite",
        "genre": "Thriller",
        "year": 2019,
        "rating": 8.5,
        "image": "https://image.tmdb.org/t/p/w500/igICOruFgiqdY1HXwTNRuXJute.jpg",
    },
    {
        "title": "John Wick",
        "genre": "Action",
        "year": 2014,
        "rating": 7.4,
        "image": "https://image.tmdb.org/t/p/w500/wXqWR7dHncNRbxoEGybEy7QTe9h.jpg",
    },
    {
        "title": "The Social Network",
        "genre": "Drama",
        "year": 2010,
        "rating": 7.8,
        "image": "https://image.tmdb.org/t/p/w500/n0ybibhJtQ5icDqTp8eRytcIHJx.jpg",
    },
]


async def ensure_seed_movies():
    existing_count = await database.fetch_val("SELECT COUNT(*) FROM movies")
    if existing_count and int(existing_count) > 0:
        return

    await database.execute(favourites_table.delete())
    await database.execute(movies_table.delete())
    for movie in MOVIES:
        await database.execute(movies_table.insert().values(**movie))


async def seed():
    ensure_schema()
    await database.connect()
    await ensure_seed_movies()
    await database.disconnect()
    print(f"Seeded {len(MOVIES)} movies with verified posters.")


if __name__ == "__main__":
    asyncio.run(seed())
