from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from models.area import Area
from models.ascent import Ascent
from models.boulder import Boulder
from schemas.boulder import BoulderWithAscentCount
from schemas.search import SearchBoulderArea


def search(db: Session, text: str):
    boulders = (
        db.execute(
            select(Boulder, func.count(Ascent.user_id).label("ascents"))
            .where(Boulder.name_normalized.ilike(f"%{text}%"))
            .join(Ascent, Ascent.boulder_id == Boulder.id)
            .options(
                joinedload(Boulder.area),
                joinedload(Boulder.grade),
                joinedload(Boulder.slash_grade),
                joinedload(Boulder.styles),
            )
            .group_by(Boulder.id)
            .order_by(Boulder.name)
            .limit(200)
        )
        .unique()
        .all()
    )

    areas = db.scalars(
        select(Area)
        .where(Area.name_normalized.ilike(f"%{text}%"))
        .order_by(Area.name)
        .limit(50)
    ).all()

    return SearchBoulderArea(
        boulders=[
            BoulderWithAscentCount.from_query_result(boulder, ascents)
            for boulder, ascents in boulders
        ],
        areas=areas,
    )
