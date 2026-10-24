from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    UniqueConstraint,
    text,
)

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
    # Role: "user" | "admin"
    Column("role", String, nullable=False, server_default="user"),
    # MFA / TOTP fields
    Column("totp_secret", String, nullable=True),
    Column("totp_enabled", Boolean, nullable=False, server_default="0"),
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
        # --- movies table migrations ---
        movie_cols = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(movies)")).fetchall()
        }
        if "rating" not in movie_cols:
            conn.execute(text("ALTER TABLE movies ADD COLUMN rating FLOAT"))
        if "image" not in movie_cols:
            conn.execute(text("ALTER TABLE movies ADD COLUMN image VARCHAR"))

        # --- users table migrations ---
        user_cols = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(users)")).fetchall()
        }
        if "role" not in user_cols:
            conn.execute(
                text("ALTER TABLE users ADD COLUMN role VARCHAR NOT NULL DEFAULT 'user'")
            )
        if "totp_secret" not in user_cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN totp_secret VARCHAR"))
        if "totp_enabled" not in user_cols:
            conn.execute(
                text("ALTER TABLE users ADD COLUMN totp_enabled BOOLEAN NOT NULL DEFAULT 0")
            )
