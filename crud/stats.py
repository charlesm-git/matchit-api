from datetime import date
from sqlalchemy import (
    Float,
    Numeric,
    and_,
    asc,
    cast,
    desc,
    func,
    select,
)
from sqlalchemy.orm import Session, selectinload
from database import MONTH_LIST
from models.area import Area
from models.boulder import Boulder
from models.crag import Crag
from models.grade import Grade
from models.ascent import Ascent
from schemas.boulder import (
    BoulderWithAscentCount,
    BoulderByGrade,
)
from schemas.general import GeneralStatistics
from schemas.grade import GradeDistribution, GradeAscents
from schemas.ascent import AscentsPerMonth, AscentsPerYear


# Home page
def get_general_statistics_home_page(db: Session):
    boulder_count = db.scalar(select(func.count(Boulder.id)))
    area_count = db.scalar(select(func.count(Area.id)))
    ascent_count = db.scalar(select(func.count(Ascent.user_id)))

    subquery = (
        select(func.avg(Grade.correspondence)).join(
            Boulder, Boulder.grade_id == Grade.id
        )
    ).scalar_subquery()

    average_grade = db.scalar(
        select(Grade).where(Grade.correspondence == func.round(subquery))
    )

    return GeneralStatistics(
        boulder_count=boulder_count,
        area_count=area_count,
        ascent_count=ascent_count,
        average_grade=average_grade,
    )


def get_general_best_rated_boulders(db: Session):
    # Get all boulders with a rating above 4.6 and more than 8 recorded ratings
    boulders = (
        db.execute(
            select(Boulder, func.count(Ascent.user_id).label("ascents"))
            .join(Boulder.ascents)
            .options(
                selectinload(Boulder.grade),
                selectinload(Boulder.crag).selectinload(Crag.area),
            )
            .where(and_(Boulder.rating >= 4.6))
            .having(func.count(Ascent.user_id) >= 8)
            .group_by(Boulder)
            .order_by(
                desc(Boulder.rating),  # Order by grade
            )
        )
        .unique()
        .all()
    )

    # Group results by grade
    grades = db.scalars(
        select(Grade).order_by(desc(Grade.correspondence))
    ).all()

    result_map = {}

    for boulder, ascents in boulders:
        grade_id = boulder.grade_id
        if grade_id not in result_map:
            result_map[grade_id] = []

        result_map[grade_id].append(
            BoulderWithAscentCount(
                id=boulder.id,
                name=boulder.name,
                name_normalized=boulder.name_normalized,
                slug=boulder.slug,
                crag=boulder.crag,
                area=boulder.crag.area,
                grade=boulder.grade,
                rating=boulder.rating,
                url=boulder.url,
                ascents=ascents,
            )
        )

    # Build final result
    result = [
        BoulderByGrade(grade=grade, boulders=result_map.get(grade.id, []))
        for grade in grades
    ]

    return result


def get_general_most_ascents_boulders(db: Session):
    # Subquery: Top 10 boulders per grade by ascent count
    ranked_boulders = (
        select(
            Boulder.id,
            Boulder.grade_id,
            func.count(Ascent.user_id).label("ascents"),
            func.row_number()
            .over(
                partition_by=Boulder.grade_id,
                order_by=desc(func.count(Ascent.user_id)),
            )
            .label("rank"),
        )
        .join(Ascent, Ascent.boulder_id == Boulder.id)
        .group_by(Boulder.id, Boulder.grade_id)
    ).subquery()

    # Main query: Get full boulder data for top 10 per grade
    boulders = (
        db.execute(
            select(Boulder, ranked_boulders.c.ascents)
            .join(ranked_boulders, Boulder.id == ranked_boulders.c.id)
            .where(ranked_boulders.c.rank <= 10)
            .options(
                selectinload(Boulder.grade),
                selectinload(Boulder.crag).selectinload(Crag.area),
            )
            .order_by(
                desc(Boulder.grade_id),  # Order by grade
                desc(
                    ranked_boulders.c.ascents
                ),  # Then by ascents within grade
            )
        )
        .unique()
        .all()
    )

    # Group results by grade
    grades = db.scalars(
        select(Grade).order_by(desc(Grade.correspondence))
    ).all()

    result_map = {}

    for boulder, ascents in boulders:
        grade_id = boulder.grade_id
        if grade_id not in result_map:
            result_map[grade_id] = []

        result_map[grade_id].append(
            BoulderWithAscentCount(
                id=boulder.id,
                name=boulder.name,
                name_normalized=boulder.name_normalized,
                slug=boulder.slug,
                crag=boulder.crag,
                area=boulder.crag.area,
                grade=boulder.grade,
                rating=boulder.rating,
                url=boulder.url,
                ascents=ascents,
            )
        )

    # Build final result
    result = [
        BoulderByGrade(grade=grade, boulders=result_map.get(grade.id, []))
        for grade in grades
    ]

    return result


# Grade based statistics
def get_general_grade_distribution(db: Session):
    result = db.execute(
        select(Grade, func.count(Boulder.id))
        .join(Boulder, Boulder.grade_id == Grade.id)
        .group_by(Grade)
        .order_by(asc(Grade.correspondence))
    ).all()

    return [
        GradeDistribution(grade=grade, boulders=boulder_count)
        for grade, boulder_count in result
    ]


def get_general_ascents_per_grade(db: Session):
    result = db.execute(
        select(Grade, func.count(Ascent.boulder_id))
        .join(Boulder, Boulder.grade_id == Grade.id)
        .join(Ascent, Boulder.id == Ascent.boulder_id)
        .group_by(Grade.id)
        .order_by(Grade.id)
    ).all()

    return [
        GradeAscents(grade=grade, ascents=ascents) for grade, ascents in result
    ]


# Time based statistics
def get_general_ascents_per_month(db: Session, grade: str = None):
    query_filter = []
    join_clause = Ascent

    if grade:
        grade_subquery = (
            select(Grade.correspondence)
            .where(Grade.value == grade)
            .scalar_subquery()
        )

        query_filter.append(Grade.correspondence >= grade_subquery)

        join_clause = Ascent.__table__.join(
            Boulder, Ascent.boulder_id == Boulder.id
        ).join(Grade, Boulder.grade_id == Grade.id)

    total_repeats = (
        select(func.count(Ascent.user_id))
        .select_from(join_clause)
        .where(*query_filter)
        .scalar_subquery()
    )
    main_query = (
        select(
            func.extract("month", Ascent.log_date).label("month"),
            func.round(
                (
                    func.count(Ascent.user_id)
                    * 100
                    / cast(total_repeats, Numeric)
                ),
                1,
            ),
        )
        .select_from(join_clause)
        .where(*query_filter)
        .group_by("month")
        .order_by("month")
    )

    result = db.execute(main_query).all()

    result_dict = {month: ascents for month, ascents in result}

    return [
        AscentsPerMonth(month=month, percentage=result_dict.get(index + 1, 0))
        for index, month in enumerate(MONTH_LIST)
    ]


def get_general_ascents_per_year(db: Session, grade: str = None):

    query_filter = []
    join_clause = Ascent

    if grade:
        grade_subquery = (
            select(Grade.correspondence)
            .where(Grade.value == grade)
            .scalar_subquery()
        )

        query_filter.append(Grade.correspondence >= grade_subquery)

        join_clause = Ascent.__table__.join(
            Boulder, Ascent.boulder_id == Boulder.id
        ).join(Grade, Boulder.grade_id == Grade.id)

    main_query = (
        select(
            func.extract("year", Ascent.log_date).label("year"),
            func.count(Ascent.user_id),
        )
        .select_from(join_clause)
        .where(
            and_(*query_filter, func.extract("year", Ascent.log_date) >= 1995)
        )
        .group_by("year")
        .order_by("year")
    )
    result = db.execute(main_query).all()

    # Convert result to dictionary for lookup
    result_dict = {int(year): ascents for year, ascents in result}

    # Single pass through years - O(n)
    current_year = date.today().year
    return [
        AscentsPerYear(year=str(year), ascents=result_dict.get(year, 0))
        for year in range(1995, current_year + 1)
    ]
