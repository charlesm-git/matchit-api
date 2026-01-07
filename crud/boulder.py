from sqlalchemy import select, func, cast, Float, case
from sqlalchemy.orm import Session, joinedload
from database import MONTH_LIST
from models.boulder import Boulder
from models.ascent import Ascent
from models.crag import Crag
from schemas.boulder import BoulderWithFullDetail
from schemas.ascent import AscentsPerMonthWithGeneral


def get_all_boulders(db: Session, skip: int = 0, limit: int = 20):
    return db.scalars(select(Boulder).offset(skip).limit(limit)).all()


def get_boulder(db: Session, id: int):
    boulder = db.scalar(
        select(Boulder)
        .where(Boulder.id == id)
        .options(
            joinedload(Boulder.grade),
            joinedload(Boulder.crag),
            joinedload(Boulder.crag).joinedload(Crag.area),
            joinedload(Boulder.ascents),
            joinedload(Boulder.ascents).joinedload(Ascent.user),
        )
    )

    # Total ascents for percentage calculation
    boulder_total_repeats = (
        select(func.count(Ascent.user_id))
        .where(Ascent.boulder_id == boulder.id)
        .scalar_subquery()
    )
    total_ascents = select(func.count(Ascent.boulder_id)).scalar_subquery()

    # Monthly ascent distribution
    aggregated_ascents = (
        db.execute(
            select(
                func.extract("month", Ascent.log_date).label("month"),
                func.round(
                    (
                        case(
                            (
                                boulder_total_repeats == 0,
                                0,
                            ),  # Handling division by 0
                            else_=(
                                func.count(
                                    case((Ascent.boulder_id == boulder.id, 1))
                                )
                                * 100
                                / cast(boulder_total_repeats, Float)
                            ),
                        )
                    )
                ).label("boulder"),
                func.round(
                    (
                        func.count(Ascent.user_id)
                        * 100
                        / cast(total_ascents, Float)
                    ),
                    1,
                ).label("general"),
            )
            .group_by("month")
            .order_by("month")
        )
        .mappings()
        .all()
    )

    aggregated_ascents = [
        AscentsPerMonthWithGeneral(
            month=MONTH_LIST[month],
            boulder=aggregated_ascents[month]["boulder"],
            general=aggregated_ascents[month]["general"],
        )
        for month in range(12)
    ]

    return BoulderWithFullDetail(
        id=boulder.id,
        name=boulder.name,
        name_normalized=boulder.name_normalized,
        rating=boulder.rating,
        url=boulder.url,
        crag=boulder.crag,
        area=boulder.crag.area,
        grade=boulder.grade,
        ascents=boulder.ascents,
        aggregated_ascents=aggregated_ascents,
    )
