from shlex import join
from sqlalchemy import and_, desc, func, select
from sqlalchemy.orm import Session, joinedload, outerjoin
from models.area import Area
from models.boulder import Boulder
from models.grade import Grade
from models.ascent import Ascent
from schemas.area import AreaStats
from schemas.boulder import BoulderWithAscentCount, BoulderWithFullDetail
from schemas.grade import GradeDistribution


def get_all_areas(db: Session, skip: int = 0, limit: int = None):
    return db.scalars(select(Area).offset(skip).limit(limit))


def get_area(db: Session, id: int):
    return db.scalar(
        select(Area).where(Area.id == id).options(joinedload(Area.region))
    )


def get_boulders_from_area(db: Session, area_id: int):
    return db.scalars(select(Boulder).where(Boulder.area_id == area_id))


def get_area_stats(db: Session, area_id: int):
    area = get_area(db, area_id)
    number_of_boulder = get_area_number_of_boulders(db, area_id)
    grade_distribution = get_area_grade_distribution(db, area_id)
    most_climbed_boulders = get_area_most_climbed_boulders(db, area_id)
    average_grade = get_area_average_grade(db, area_id)
    ascents = get_area_total_ascents(db, area_id)
    best_rated_boulders = get_area_best_rated(db, area_id)
    return AreaStats(
        area=area,
        number_of_boulders=number_of_boulder,
        grade_distribution=grade_distribution,
        most_climbed_boulders=most_climbed_boulders,
        average_grade=average_grade,
        ascents=ascents,
        best_rated_boulders=best_rated_boulders,
    )


def get_area_name_from_id(db: Session, area_id: int):
    return db.scalar(select(Area.name).where(Area.id == area_id))


def get_area_number_of_boulders(db: Session, area_id: int):
    return db.scalar(
        select(func.count(Boulder.id)).where(Boulder.area_id == area_id)
    )


def get_area_grade_distribution(db: Session, area_id: int):
    result = db.execute(
        select(Grade, func.count(Boulder.id))
        .select_from(
            outerjoin(
                Grade,
                Boulder,
                (Boulder.grade_id == Grade.id) & (Boulder.area_id == area_id),
            )
        )
        .group_by(Grade.id)
    ).all()

    return [
        GradeDistribution(grade=grade, boulders=boulders)
        for grade, boulders in result
    ]


def get_area_most_climbed_boulders(db: Session, area_id: int, limit: int = 10):
    result = (
        db.execute(
            select(
                Boulder,
                func.count(Ascent.user_id).label("ascents"),
            )
            .where(Boulder.area_id == area_id)
            .options(
                joinedload(Boulder.grade),
                joinedload(Boulder.slash_grade),
                joinedload(Boulder.area),
                joinedload(Boulder.styles),
            )
            .order_by(desc("ascents"))
            .join(Ascent, Boulder.id == Ascent.boulder_id)
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


def get_area_average_grade(db: Session, area_id: int):
    subquery = (
        select(func.avg(Grade.correspondence))
        .where(Boulder.area_id == area_id)
        .join(Boulder, Boulder.grade_id == Grade.id)
    ).scalar_subquery()

    result = db.scalar(
        select(Grade).where(Grade.correspondence == func.round(subquery))
    )

    if not result:
        return None
    return result


def get_area_total_ascents(db: Session, area_id: int):
    return db.scalar(
        select(func.count(Ascent.user_id))
        .where(Boulder.area_id == area_id)
        .join(Boulder, Boulder.id == Ascent.boulder_id)
    )


def get_area_best_rated(db: Session, area_id: int):
    result = (
        db.execute(
            select(Boulder, func.count(Ascent.user_id).label("ascents"))
            .filter(
                and_(
                    Boulder.area_id == area_id,
                    Boulder.number_of_rating >= 5,
                )
            )
            .options(
                joinedload(Boulder.grade),
                joinedload(Boulder.slash_grade),
                joinedload(Boulder.area),
                joinedload(Boulder.styles),
            )
            .join(Ascent, Boulder.id == Ascent.boulder_id)
            .group_by(Boulder.id)
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
