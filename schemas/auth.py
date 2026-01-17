"""
Pydantic schemas for authentication endpoints.
"""

from pydantic import BaseModel, Field


class SignupRequest(BaseModel):
    """Request schema for user signup."""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    """Request schema for user login."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """Response schema for token generation."""

    access_token: str
    token_type: str = "bearer"


class AccountResponse(BaseModel):
    """Response schema for account information."""

    id: int
    username: str

    class Config:
        from_attributes = True
