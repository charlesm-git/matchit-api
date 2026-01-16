from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from crud.crag import get_boulders_from_crag, get_crag, get_crag_stats
from database import get_db_session
from schemas.boulder import Boulder
from schemas.crag import Crag, CragStats

router = APIRouter(prefix="/crag", tags=["crag"])


@router.get("/{slug}")
def read_crag(
    slug: str,
    db: Session = Depends(get_db_session),
) -> Crag:
    crag = get_crag(db=db, slug=slug)
    if not crag:
        raise HTTPException(status_code=404, detail="Crag not found")
    return crag


@router.get("/{slug}/boulders")
def read_boulders_from_area(
    slug: str, db: Session = Depends(get_db_session)
) -> List[Boulder]:
    boulders = get_boulders_from_crag(db=db, crag_slug=slug)
    return boulders


@router.get("/{slug}/stats")
def read_area_stats(
    slug: str, db: Session = Depends(get_db_session)
) -> CragStats:
    return get_crag_stats(db=db, crag_slug=slug)
