from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from crud.area import (
    get_all_areas,
    get_area,
    get_area_stats,
    get_boulders_from_area,
)
from database import get_db_session
from schemas.area import Area, AreaDetail, AreaStats
from schemas.boulder import Boulder

router = APIRouter(prefix="/area", tags=["area"])


@router.get("")
def read_areas(
    skip: int = Query(0, ge=0),
    limit: int = Query(None),
    db: Session = Depends(get_db_session),
) -> List[Area]:
    return get_all_areas(db=db, skip=skip, limit=limit)


@router.get("/{id}")
def read_area(
    id: int,
    db: Session = Depends(get_db_session),
) -> AreaDetail:
    boulder = get_area(db=db, id=id)
    return boulder


@router.get("/{id}/boulders")
def read_boulders_from_area(
    id: int, db: Session = Depends(get_db_session)
) -> List[Boulder]:
    boulders = get_boulders_from_area(db=db, area_id=id)
    return boulders


@router.get("/{id}/stats")
def read_area_stats(
    id: int, db: Session = Depends(get_db_session)
) -> AreaStats:
    return get_area_stats(db=db, area_id=id)
