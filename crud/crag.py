from sqlalchemy import and_, desc, func, select
from sqlalchemy.orm import Session, selectinload
from models.boulder import Boulder
from models.crag import Crag
from models.grade import Grade
from models.ascent import Ascent
from schemas.boulder import BoulderWithAscentCount
from schemas.crag import CragStats
from schemas.grade import GradeDistribution


def get_crag(db: Session, slug: str):
    return db.scalar(
        select(Crag).where(Crag.slug == slug).options(selectinload(Crag.area))
    )


def get_boulders_from_crag(db: Session, slug: str):
    return db.scalars(
        select(Boulder).join(Boulder.crag).where(Crag.slug == slug)
    )


def get_crag_stats(db: Session, crag_slug: str):
    crag = get_crag(db, crag_slug)
    number_of_boulder = get_crag_number_of_boulders(db, crag_slug)
    grade_distribution = get_crag_grade_distribution(db, crag_slug)
    most_climbed_boulders = get_crag_most_climbed_boulders(db, crag_slug)
    average_grade = get_crag_average_grade(db, crag_slug)
    ascents = get_crag_total_ascents(db, crag_slug)
    best_rated_boulders = get_crag_best_rated(db, crag_slug)
    return CragStats(
        crag=crag,
        number_of_boulders=number_of_boulder,
        grade_distribution=grade_distribution,
        most_climbed_boulders=most_climbed_boulders,
        average_grade=average_grade,
        ascents=ascents,
        best_rated_boulders=best_rated_boulders,
    )


def get_crag_name_from_slug(db: Session, crag_slug: str):
    return db.scalar(select(Crag.name).where(Crag.slug == crag_slug))


def get_crag_number_of_boulders(db: Session, crag_slug: str):
    return db.scalar(
        select(func.count(Boulder.id))
        .join(Boulder.crag)
        .where(Crag.slug == crag_slug)
    )


def get_crag_grade_distribution(db: Session, crag_slug: str):
    result = db.execute(
        select(Grade, func.count(Boulder.id))
        .select_from(Grade)
        .outerjoin(Boulder, Boulder.grade_id == Grade.id)
        .outerjoin(Crag, Boulder.crag_id == Crag.id)
        .where(and_(Grade.correspondence >= 12, Crag.slug == crag_slug))
        .group_by(Grade.id)
    ).all()

    return [
        GradeDistribution(grade=grade, boulders=boulders)
        for grade, boulders in result
    ]


def get_crag_most_climbed_boulders(
    db: Session, crag_slug: str, limit: int = 20
):
    result = (
        db.execute(
            select(
                Boulder,
                func.count(Ascent.user_id).label("ascents"),
            )
            .join(Boulder.crag)
            .join(Boulder.ascents)
            .where(Crag.slug == crag_slug)
            .options(
                selectinload(Boulder.grade),
                selectinload(Boulder.crag).selectinload(Crag.area),
            )
            .order_by(desc("ascents"))
            .group_by(Boulder)
            .limit(limit)
        )
        .unique()
        .all()
    )

    return [
        BoulderWithAscentCount.from_query_result(boulder, ascents)
        for boulder, ascents in result
    ]


def get_crag_average_grade(db: Session, crag_slug: str):
    subquery = (
        select(func.avg(Grade.correspondence))
        .select_from(Boulder)
        .join(Boulder.grade)
        .join(Boulder.crag)
        .where(Crag.slug == crag_slug)
    ).scalar_subquery()

    result = db.scalar(
        select(Grade).where(Grade.correspondence == func.round(subquery))
    )

    if not result:
        return None
    return result


def get_crag_total_ascents(db: Session, crag_slug: str):
    return db.scalar(
        select(func.count(Ascent.user_id))
        .join(Boulder, Boulder.id == Ascent.boulder_id)
        .join(Boulder.crag)
        .where(Crag.slug == crag_slug)
    )


def get_crag_best_rated(db: Session, crag_slug: str):
    result = (
        db.execute(
            select(Boulder, func.count(Ascent.user_id).label("ascents"))
            .join(Ascent, Boulder.id == Ascent.boulder_id)
            .join(Boulder.crag)
            .where(Crag.slug == crag_slug)
            .options(
                selectinload(Boulder.grade),
                selectinload(Boulder.crag).selectinload(Crag.area),
            )
            .group_by(Boulder)
            .having(func.count(Ascent.user_id) >= 15)
            .order_by(desc(Boulder.rating))
            .limit(20)
        )
        .unique()
        .all()
    )

    return [
        BoulderWithAscentCount.from_query_result(boulder, ascents)
        for boulder, ascents in result
    ]
