import databases
from sqlalchemy import MetaData, create_engine

DATABASE_URL = "sqlite:///./movies.db"

database = databases.Database(DATABASE_URL)
metadata = MetaData()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
