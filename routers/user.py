from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db_session
from crud.user import (
    get_all_users,
    get_user,
    get_user_boulders_set,
    get_user_boulders_repeated,
    get_user_stats,
)
from schemas.user import User, UserDetail, UserStats
from schemas.boulder import Boulder

router = APIRouter(prefix="/user", tags=["user"])


@router.get("")
def read_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db_session),
    username: str = None,
) -> List[User]:
    return get_all_users(db=db, skip=skip, limit=limit, username=username)


@router.get("/{id}")
def read_user(
    id: int,
    db: Session = Depends(get_db_session),
) -> UserDetail:
    boulder = get_user(db=db, id=id)
    return boulder


@router.get("/{id}/boulder/set")
def read_boulders_set_by(
    id: int, db: Session = Depends(get_db_session)
) -> List[Boulder]:
    boulders = get_user_boulders_set(db=db, user_id=id)
    return boulders


@router.get("/{id}/boulder/ascent")
def read_boulders_repeated_by(
    id: int, db: Session = Depends(get_db_session)
) -> List[Boulder]:
    boulders = get_user_boulders_repeated(db=db, user_id=id)
    return boulders


@router.get("/{id}/stats")
def read_user_stats(
    id: int, db: Session = Depends(get_db_session)
) -> UserStats:
    return get_user_stats(db=db, user_id=id)
