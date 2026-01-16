from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
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


@router.get("/{slug}")
def read_area(
    slug: str,
    db: Session = Depends(get_db_session),
) -> AreaDetail:
    area = get_area(db=db, slug=slug)
    if not area:
        raise HTTPException(status_code=404, detail="Area not found")
    return area


@router.get("/{slug}/boulders")
def read_boulders_from_area(
    slug: str, db: Session = Depends(get_db_session)
) -> List[Boulder]:
    boulders = get_boulders_from_area(db=db, slug=slug)
    return boulders


@router.get("/{slug}/stats")
def read_area_stats(
    slug: str, db: Session = Depends(get_db_session)
) -> AreaStats:
    return get_area_stats(db=db, area_slug=slug)