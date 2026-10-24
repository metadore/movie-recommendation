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
    role: str = "user"  # "user" or "admin"


class UserLogin(BaseModel):
    username: str
    password: str
    totp_code: str | None = None  # optional – required only when MFA is enabled


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str = "user"
    mfa_required: bool = False   # True → client must POST /api/auth/mfa-verify


class MFASetupOut(BaseModel):
    totp_uri: str        # provisioning URI for the authenticator app
    secret: str          # base-32 secret (show to user once)


class MFAVerifyIn(BaseModel):
    code: str            # 6-digit TOTP code


class UserOut(BaseModel):
    id: int
    username: str
    role: str = "user"
    totp_enabled: bool = False


class RecommendOut(BaseModel):
    id: int | None = None
    title: str
    genre: str | None = None
    year: int | None = None
    rating: float | None = None
    image: str | None = None
    reason: str | None = None
