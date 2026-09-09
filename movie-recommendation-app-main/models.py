from sqlalchemy import Column, Float, ForeignKey, Integer, String, Table, UniqueConstraint, text

from database import engine, metadata

movies_table = Table(
    "movies",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("title", String, nullable=False),
    Column("genre", String, nullable=False),
    Column("year", Integer, nullable=False),
    Column("rating", Float),
    Column("image", String),
)

users_table = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String, nullable=False, unique=True),
    Column("password_hash", String, nullable=False),
)

favourites_table = Table(
    "favourites",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("movie_id", Integer, ForeignKey("movies.id"), nullable=False),
    UniqueConstraint("user_id", "movie_id", name="uq_user_movie"),
)


def ensure_schema() -> None:
    metadata.create_all(engine)
    with engine.begin() as conn:
        cols = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(movies)")).fetchall()
        }
        if "rating" not in cols:
            conn.execute(text("ALTER TABLE movies ADD COLUMN rating FLOAT"))
        if "image" not in cols:
            conn.execute(text("ALTER TABLE movies ADD COLUMN image VARCHAR"))
