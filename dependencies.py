"""
FastAPI dependencies for authentication and authorization.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from helper import decode_access_token
from database import get_db_session
from models.account import Account

security = HTTPBearer()


def get_current_account(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db_session),
) -> Account:
    """
    Dependency to get the current authenticated account from JWT token.

    Use this as a dependency in any route that requires authentication.

    Example:
        @router.get("/protected")
        def protected_route(account: Account = Depends(get_current_account)):
            return {"message": f"Hello {account.username}"}

    Args:
        credentials: HTTP Authorization header with Bearer token
        db: Database session

    Returns:
        Account object of the authenticated user

    Raises:
        HTTPException: 401 if token is invalid or account not found
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    account_id = payload.get("sub")
    if account_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    account = Account.get_by_id(db, int(account_id))
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return account
