import numpy as np
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from crud.recommendation import get_recommended_boulder, get_selected_boulder
from database import get_db_session, get_recommendation_matrices
from schemas.boulder import BoulderWithAscentCount
from schemas.recommendation import RecommendationRequest


router = APIRouter(prefix="/recommendation", tags=["recommendation"])


@router.post("")
def post_recommendation(
    request: RecommendationRequest,
    db: Session = Depends(get_db_session),
    matrices=Depends(get_recommendation_matrices),
) -> List[BoulderWithAscentCount]:

    recommended_boulder_ids = recommendation_extraction_algorithm(
        boulder_ids=request.boulder_ids,
        ascent_weight=request.ascent_weight,
        grade_weight=request.grade_weight,
        style_weight=request.style_weight,
        top_N=request.top_N,
        matrices=matrices,
    )
    # Retrieve recommended boulders from the database
    recommended_boulders = get_recommended_boulder(
        db=db, boulder_ids=recommended_boulder_ids
    )

    # Order recommended boulders
    recommended_boulders = {
        boulder.id: boulder for boulder in recommended_boulders
    }
    ordered_boulders = [
        recommended_boulders[boulder_id]
        for boulder_id in recommended_boulder_ids
    ]

    return ordered_boulders


@router.get("/load-matrices")
def get_matrices(matrices=Depends(get_recommendation_matrices)):
    return


@router.get("/selection")
def get_searched_boulders(
    q: str = "",
    db: Session = Depends(get_db_session),
) -> List[BoulderWithAscentCount]:
    if not q or not q.strip():
        return []
    boulders = get_selected_boulder(db=db, text=q)
    return boulders


def recommendation_extraction_algorithm(
    boulder_ids, ascent_weight, grade_weight, style_weight, top_N, matrices
):
    # Get similarity matrices
    ascents, style, grade = matrices

    ascents = ascents[:, boulder_ids].sum(axis=1).A1
    style = style[:, boulder_ids].sum(axis=1).A1
    grade = grade[:, boulder_ids].sum(axis=1).A1

    # Remove input boulders from the recommendation
    ascents[boulder_ids] = 0
    style[boulder_ids] = 0
    grade[boulder_ids] = 0

    # Compute total similarity score
    sim_scores = (
        ascent_weight * ascents + style_weight * style + grade_weight * grade
    )

    # Get the top N most similar boulders for recommendation
    recommended_boulder_ids = np.argsort(-sim_scores)[:top_N]
    recommended_boulder_ids = recommended_boulder_ids.tolist()

    return recommended_boulder_ids
