from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from crud import area
from crud.recommendation import get_recommended_boulder, get_selected_boulder
from database import get_db_session
from schemas.boulder import BoulderWithAscentCount
from schemas.recommendation import RecommendationRequest


router = APIRouter(prefix="/recommendation", tags=["recommendation"])


@router.post("")
def post_recommendation(
    request: RecommendationRequest,
    db: Session = Depends(get_db_session),
) -> List[BoulderWithAscentCount]:

    # Retrieve recommended boulders from the database
    recommended_boulders = get_recommended_boulder(
        db=db, boulder_ids=request.boulder_ids
    )

    return recommended_boulders


@router.get("/selection/{area_slug}")
def get_searched_boulders(
    area_slug: str,
    q: str = "",
    db: Session = Depends(get_db_session),
) -> List[BoulderWithAscentCount]:
    if not q or not q.strip():
        return []
    boulders = get_selected_boulder(db=db, area_slug=area_slug, text=q)
    return boulders
