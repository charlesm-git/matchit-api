from typing import Union
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from crud.search import search
from database import get_db_session
from helper import text_normalizer
from schemas.search import SearchBoulderArea


router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
def read_research(
    q: str = "",
    db: Session = Depends(get_db_session),
) -> SearchBoulderArea:
    if not q or not q.strip():
        return SearchBoulderArea(boulders=[], areas=[])
    
    return search(db=db, text=text_normalizer(q))
