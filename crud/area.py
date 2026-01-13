from sqlalchemy import and_, desc, func, select
from sqlalchemy.orm import Session, joinedload, contains_eager
from models.area import Area
from models.boulder import Boulder
from models.crag import Crag
from models.grade import Grade
from models.ascent import Ascent
from schemas.area import AreaStats
from schemas.boulder import BoulderWithAscentCount
from schemas.grade import GradeDistribution


def get_all_areas(db: Session, skip: int = 0, limit: int = None):
    return db.scalars(select(Area).offset(skip).limit(limit))


def get_area(db: Session, slug: str):
    return db.scalar(
        select(Area)
        .outerjoin(Area.crags)
        .where(Area.slug == slug)
        .where(Crag.boulders.any())
        .options(contains_eager(Area.crags))
    )


def get_boulders_from_area(db: Session, slug: str):
    return db.scalars(
        select(Boulder)
        .join(Boulder.crag)
        .where(Crag.area.has(Area.slug == slug))
    )


def get_area_stats(db: Session, area_slug: str):
    area = get_area(db, area_slug)
    number_of_boulder = get_area_number_of_boulders(db, area_slug)
    grade_distribution = get_area_grade_distribution(db, area_slug)
    most_climbed_boulders = get_area_most_climbed_boulders(db, area_slug)
    average_grade = get_area_average_grade(db, area_slug)
    ascents = get_area_total_ascents(db, area_slug)
    best_rated_boulders = get_area_best_rated(db, area_slug)
    return AreaStats(
        area=area,
        number_of_boulders=number_of_boulder,
        grade_distribution=grade_distribution,
        most_climbed_boulders=most_climbed_boulders,
        average_grade=average_grade,
        ascents=ascents,
        best_rated_boulders=best_rated_boulders,
    )


def get_area_name_from_slug(db: Session, area_slug: str):
    return db.scalar(select(Area.name).where(Area.slug == area_slug))


def get_area_number_of_boulders(db: Session, area_slug: str):
    return db.scalar(
        select(func.count(Boulder.id))
        .join(Boulder.crag)
        .where(Crag.area.has(Area.slug == area_slug))
    )


def get_area_grade_distribution(db: Session, area_slug: str):
    result = db.execute(
        select(Grade, func.count(Boulder.id))
        .select_from(Grade)
        .outerjoin(Boulder, Boulder.grade_id == Grade.id)
        .outerjoin(Crag, Boulder.crag_id == Crag.id)
        .outerjoin(Area, Crag.area_id == Area.id)
        .where(and_(Grade.correspondence >= 12, Area.slug == area_slug))
        .group_by(Grade.id)
    ).all()

    return [
        GradeDistribution(grade=grade, boulders=boulders)
        for grade, boulders in result
    ]


def get_area_most_climbed_boulders(
    db: Session, area_slug: str, limit: int = 10
):
    result = (
        db.execute(
            select(
                Boulder,
                func.count(Ascent.user_id).label("ascents"),
            )
            .join(Boulder.crag)
            .join(Boulder.ascents)
            .where(Crag.area.has(Area.slug == area_slug))
            .options(
                joinedload(Boulder.grade),
                joinedload(Boulder.crag).joinedload(Crag.area),
            )
            .order_by(desc("ascents"))
            .group_by(Ascent.boulder_id)
            .limit(limit)
        )
        .unique()
        .all()
    )

    return [
        BoulderWithAscentCount.from_query_result(boulder, ascents)
        for boulder, ascents in result
    ]


def get_area_average_grade(db: Session, area_slug: str):
    subquery = (
        select(func.avg(Grade.correspondence))
        .select_from(Boulder)
        .join(Boulder.grade)
        .join(Boulder.crag)
        .where(Crag.area.has(Area.slug == area_slug))
    ).scalar_subquery()

    result = db.scalar(
        select(Grade).where(Grade.correspondence == func.round(subquery))
    )

    if not result:
        return None
    return result


def get_area_total_ascents(db: Session, area_slug: str):
    return db.scalar(
        select(func.count(Ascent.user_id))
        .join(Boulder, Boulder.id == Ascent.boulder_id)
        .join(Boulder.crag)
        .where(Crag.area.has(Area.slug == area_slug))
    )


def get_area_best_rated(db: Session, area_slug: str):
    result = (
        db.execute(
            select(Boulder, func.count(Ascent.user_id).label("ascents"))
            .join(Ascent, Boulder.id == Ascent.boulder_id)
            .join(Boulder.crag)
            .where(Crag.area.has(Area.slug == area_slug))
            .options(
                joinedload(Boulder.grade),
                joinedload(Boulder.crag).joinedload(Crag.area),
            )
            .group_by(Boulder.id)
            .having(func.count(Ascent.user_id) >= 15)
            .order_by(desc(Boulder.rating))
            .limit(15)
        )
        .unique()
        .all()
    )

    return [
        BoulderWithAscentCount.from_query_result(boulder, ascents)
        for boulder, ascents in result
    ]
