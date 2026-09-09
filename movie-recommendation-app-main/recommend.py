from database import database
from gemini_api import suggest_related_genres
from models import favourites_table, movies_table


def _row_to_rec(row, reason: str) -> dict:
    data = dict(row)
    data["reason"] = reason
    return data


async def favourite_genres(user_id: int) -> list[str]:
    query = (
        movies_table.select()
        .select_from(
            favourites_table.join(
                movies_table, favourites_table.c.movie_id == movies_table.c.id
            )
        )
        .where(favourites_table.c.user_id == user_id)
    )
    rows = await database.fetch_all(query)
    genres: list[str] = []
    for row in rows:
        g = (row["genre"] or "").strip()
        if g and g.lower() not in {x.lower() for x in genres}:
            genres.append(g)
    return genres


async def recommend_movies(
    seed: str,
    user_id: int | None = None,
    limit: int = 6,
) -> list[dict]:
    seed = (seed or "").strip()
    all_movies = [dict(r) for r in await database.fetch_all(movies_table.select())]
    if not all_movies:
        return []

    seed_movie = None
    if seed:
        lowered = seed.lower()
        for movie in all_movies:
            if lowered in movie["title"].lower():
                seed_movie = movie
                break

    target_genres: list[str] = []
    exclude_ids: set[int] = set()

    if seed_movie:
        exclude_ids.add(seed_movie["id"])
        if seed_movie.get("genre"):
            target_genres.append(seed_movie["genre"])
        for g in suggest_related_genres(seed_movie["title"], seed_movie.get("genre")):
            if g.lower() not in {x.lower() for x in target_genres}:
                target_genres.append(g)
    elif seed:
        target_genres.append(seed)
        for g in suggest_related_genres(seed):
            if g.lower() not in {x.lower() for x in target_genres}:
                target_genres.append(g)

    if user_id is not None:
        for g in await favourite_genres(user_id):
            if g.lower() not in {x.lower() for x in target_genres}:
                target_genres.append(g)

    scored: list[tuple[float, dict, str]] = []
    for movie in all_movies:
        if movie["id"] in exclude_ids:
            continue
        genre = (movie.get("genre") or "").lower()
        score = float(movie.get("rating") or 0)
        reason = "Top rated pick"
        for idx, target in enumerate(target_genres):
            if target.lower() in genre or genre in target.lower():
                score += 20 - idx
                reason = f"Similar to your taste ({target})"
                break
        if seed and seed.lower() in (movie.get("title") or "").lower():
            continue
        scored.append((score, movie, reason))

    scored.sort(key=lambda item: item[0], reverse=True)
    results = [_row_to_rec(movie, reason) for _, movie, reason in scored[:limit]]

    if not results:
        top = sorted(all_movies, key=lambda m: m.get("rating") or 0, reverse=True)
        results = [_row_to_rec(m, "Popular in catalog") for m in top[:limit]]

    return results
