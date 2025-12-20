from sqlalchemy import select, func, cast, Float, case
from sqlalchemy.orm import Session, joinedload
from database import MONTH_LIST
from models.boulder_style import boulder_style_table
from models.boulder import Boulder
from models.ascent import Ascent
from models.style import Style
from schemas.boulder import BoulderWithFullDetail
from schemas.ascent import AscentsPerMonthWithGeneral


def get_all_boulders(db: Session, skip: int = 0, limit: int = 20, style=None):
    query = select(Boulder)
    if style:
        query = (
            query.where(Style.style == style)
            .join(
                boulder_style_table,
                Boulder.id == boulder_style_table.c.boulder_id,
            )
            .join(Style, Style.id == boulder_style_table.c.style_id)
        )
    return db.scalars(query.offset(skip).limit(limit))


def get_boulder(db: Session, id: int):
    boulder = db.scalar(
        select(Boulder)
        .where(Boulder.id == id)
        .options(
            joinedload(Boulder.grade),
            joinedload(Boulder.slash_grade),
            joinedload(Boulder.area),
            joinedload(Boulder.styles),
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
        rating=boulder.rating,
        number_of_rating=boulder.number_of_rating,
        url=boulder.url,
        grade=boulder.grade,
        slash_grade=boulder.slash_grade,
        area=boulder.area,
        styles=boulder.styles,
        ascents=boulder.ascents,
        aggregated_ascents=aggregated_ascents,
    )
