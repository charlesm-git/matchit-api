from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from crud.boulder import get_all_boulders, get_boulder
from database import get_db_session
from schemas.boulder import Boulder, BoulderWithFullDetail

router = APIRouter(prefix="/boulder", tags=["boulder"])


@router.get("")
def read_boulders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db_session),
    style: str = None,
) -> List[Boulder]:
    return get_all_boulders(db=db, skip=skip, limit=limit, style=style)


@router.get("/{id}")
def read_boulder(
    id: int,
    db: Session = Depends(get_db_session),
) -> BoulderWithFullDetail:
    boulder = get_boulder(db=db, id=id)
    return boulder
