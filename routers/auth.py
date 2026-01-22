from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from crud.auth import create_account, authenticate_account
from database import get_db_session
from models.account import Account
from schemas.auth import (
    SignupRequest,
    LoginRequest,
    TokenResponse,
    AccountResponse,
)
from helper import create_access_token
from dependencies import get_current_account

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
)
def signup(
    request: SignupRequest,
    db: Session = Depends(get_db_session),
) -> AccountResponse:
    """
    Register a new account.

    Creates a new account with the provided username and password.
    Password is hashed using Argon2 before storage.
    """
    try:
        account = create_account(db, request.username, request.password)
        return account
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.post("/login")
def login(
    request: LoginRequest,
    db: Session = Depends(get_db_session),
) -> TokenResponse:
    """
    Authenticate and receive JWT token.

    Validates credentials and returns a JWT access token.
    Token should be included in Authorization header as 'Bearer <token>' for protected routes.
    """
    account = authenticate_account(db, request.username, request.password)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create JWT token with account ID as subject
    access_token = create_access_token(
        data={"sub": str(account.id), "username": account.username}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me")
def get_current_user(
    account: Account = Depends(get_current_account),
) -> AccountResponse:
    """
    Get current authenticated account information.

    Requires valid JWT token in Authorization header.
    """
    return account
