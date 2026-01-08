from typing import List
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload

from helper import text_normalizer
from models.ascent import Ascent
from models.boulder import Boulder
from models.crag import Crag
from models.similarity import Similarity
from schemas.boulder import BoulderWithAscentCount, RecommendationOutput


def get_recommended_boulder(db: Session, boulder_ids: List[int]):
    # Subquery for ascent counts to avoid join multiplication
    ascent_subquery = (
        select(
            Ascent.boulder_id, func.count(Ascent.user_id).label("ascent_count")
        )
        .group_by(Ascent.boulder_id)
        .subquery()
    )

    result = (
        db.execute(
            select(
                Boulder,
                func.coalesce(ascent_subquery.c.ascent_count, 0).label(
                    "ascents"
                ),
                func.sum(Similarity.score).label("score"),
            )
            .join(Similarity, Similarity.id2 == Boulder.id)
            .outerjoin(
                ascent_subquery, ascent_subquery.c.boulder_id == Boulder.id
            )
            .where(Similarity.id1.in_(boulder_ids))
            .options(
                joinedload(Boulder.grade),
                joinedload(Boulder.crag).joinedload(Crag.area),
            )
            .group_by(Boulder.id)
            .order_by(desc("score"))
            .limit(50)
        )
        .unique()
        .all()
    )

    return [
        RecommendationOutput(
            id=boulder.id,
            name=boulder.name,
            name_normalized=boulder.name_normalized,
            crag=boulder.crag,
            area=boulder.crag.area,
            grade=boulder.grade,
            rating=boulder.rating,
            url=boulder.url,
            ascents=ascents,
            score=score,
        )
        for boulder, ascents, score in result
    ]


def get_selected_boulder(db: Session, text: str):
    normalized_text = text_normalizer(text)
    result = (
        db.execute(
            select(Boulder, func.count(Ascent.user_id).label("ascents"))
            .where(Boulder.name_normalized.ilike(f"%{normalized_text}%"))
            .outerjoin(Ascent, Ascent.boulder_id == Boulder.id)
            .options(
                joinedload(Boulder.grade),
                joinedload(Boulder.crag).joinedload(Crag.area),
            )
            .group_by(Boulder.id)
            .limit(20)
        )
        .unique()
        .all()
    )
    return [
        BoulderWithAscentCount(
            id=boulder.id,
            name=boulder.name,
            name_normalized=boulder.name_normalized,
            crag=boulder.crag,
            area=boulder.crag.area,
            grade=boulder.grade,
            rating=boulder.rating,
            url=boulder.url,
            ascents=ascents,
        )
        for boulder, ascents in result
    ]
