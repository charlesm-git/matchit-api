from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from models.area import Area
from models.ascent import Ascent
from models.boulder import Boulder
from models.crag import Crag
from schemas.boulder import BoulderWithAscentCount
from schemas.search import SearchOutput


def search(db: Session, text: str):
    boulders = (
        db.execute(
            select(Boulder, func.count(Ascent.user_id).label("ascents"))
            .where(Boulder.name_normalized.ilike(f"%{text}%"))
            .join(Ascent, Ascent.boulder_id == Boulder.id)
            .options(
                joinedload(Boulder.grade),
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
        .limit(10)
    ).all()

    crags = db.scalars(
        select(Crag)
        .where(Crag.name_normalized.ilike(f"%{text}%"))
        .order_by(Crag.name)
        .limit(20)
    ).all()

    return SearchOutput(
        boulders=[
            BoulderWithAscentCount.from_query_result(boulder, ascents)
            for boulder, ascents in boulders
        ],
        areas=areas,
        crags=crags,
    )
