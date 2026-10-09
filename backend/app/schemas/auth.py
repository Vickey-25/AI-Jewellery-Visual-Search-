from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: str
    phone: str | None = None
    is_active: bool
    created_at: datetime | None = None


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    full_name: str = Field(..., min_length=2, max_length=100)
    role: str = Field("customer", pattern="^(customer|shopowner)$")
    phone: str | None = Field(None, max_length=50)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=100)
    role: str | None = Field(None, pattern="^(customer|shopowner)$")


class AuthResponse(BaseModel):
    token: str
    user: UserOut
