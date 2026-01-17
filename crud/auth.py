"""
CRUD operations for authentication.
"""

from sqlalchemy.orm import Session
from sqlalchemy import select
from models.account import Account
from helper import hash_password, verify_password
from typing import Optional


def create_account(db: Session, username: str, password: str) -> Account:
    """
    Create a new account with hashed password.

    Args:
        db: Database session
        username: Username for the account
        password: Plain text password (will be hashed)

    Returns:
        Created Account object

    Raises:
        ValueError: If username already exists
    """
    # Check if username already exists
    existing = db.scalar(select(Account).where(Account.username == username))
    if existing:
        raise ValueError("Username already exists")

    # Hash password and create account
    hashed = hash_password(password)
    account = Account(username=username, password_hash=hashed)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def authenticate_account(
    db: Session, username: str, password: str
) -> Optional[Account]:
    """
    Authenticate an account by username and password.

    Args:
        db: Database session
        username: Username to authenticate
        password: Plain text password to verify

    Returns:
        Account object if authentication successful, None otherwise
    """
    account = db.query(Account).filter(Account.username == username).first()
    if not account:
        return None

    if not verify_password(password, account.password_hash):
        return None

    return account
