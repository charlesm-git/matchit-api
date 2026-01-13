from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from crud.country import get_all_countries_with_areas, get_countries
from database import get_db_session
from schemas.country import Country, CountryDetail

router = APIRouter(prefix="/country", tags=["country"])


@router.get("")
def read_countries(
    db: Session = Depends(get_db_session),
) -> List[Country]:
    return get_countries(db=db)

@router.get("/details")
def read_countries_with_areas(
    limit: int = Query(None),
    db: Session = Depends(get_db_session),
) -> List[CountryDetail]:
    return get_all_countries_with_areas(db=db, limit=limit)