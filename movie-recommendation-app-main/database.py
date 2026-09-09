import os
from pathlib import Path

import databases
from sqlalchemy import MetaData, create_engine


def get_database_url() -> str:
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url

    if os.getenv("VERCEL"):
        return "sqlite:////tmp/movies.db"

    base_dir = Path(__file__).resolve().parent
    return f"sqlite:///{base_dir / 'movies.db'}"


DATABASE_URL = get_database_url()

database = databases.Database(DATABASE_URL)
metadata = MetaData()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
