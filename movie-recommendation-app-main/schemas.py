from pydantic import BaseModel, Field


class MovieCreate(BaseModel):
    title: str
    genre: str
    year: int
    rating: float | None = None
    image: str | None = None


class MovieOut(MovieCreate):
    id: int


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=4, max_length=128)


class UserLogin(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class UserOut(BaseModel):
    id: int
    username: str


class RecommendOut(BaseModel):
    id: int | None = None
    title: str
    genre: str | None = None
    year: int | None = None
    rating: float | None = None
    image: str | None = None
    reason: str | None = None
