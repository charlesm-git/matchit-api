from calendar import month
from datetime import date
from sqlalchemy import (
    Float,
    and_,
    asc,
    cast,
    desc,
    exists,
    func,
    select,
    case,
)
from sqlalchemy.orm import Session, joinedload
from database import MONTH_LIST
from models.area import Area
from models.boulder import Boulder
from models.boulder_style import boulder_style_table
from models.boulder_setter import boulder_setter_table
from models.grade import Grade
from models.ascent import Ascent
from models.style import Style
from models.user import User
from schemas.area import AreaCount
from schemas.boulder import (
    BoulderWithAscentCount,
    BoulderByGrade,
)
from schemas.general import GeneralStatistics
from schemas.grade import GradeDistribution, GradeAscents
from schemas.ascent import AscentsPerMonth, AscentsPerYear
from schemas.style import StyleDistribution
from schemas.user import UserBoulderCount, UserAscentVolume


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


# Best rated boulders
def get_general_best_rated_boulders_per_grade(db: Session, grade: str):
    result = (
        db.execute(
            select(Boulder, func.count(Ascent.user_id).label("ascents"))
            .where(
                and_(
                    Grade.value == grade,
                    Boulder.number_of_rating >= 10,
                    Boulder.rating >= 4.6,
                )
            )
            .join(Grade, Boulder.grade_id == Grade.id)
            .join(Ascent, Ascent.boulder_id == Boulder.id)
            .options(
                joinedload(Boulder.area),
                joinedload(Boulder.styles),
                joinedload(Boulder.grade),
                joinedload(Boulder.slash_grade),
            )
            .group_by(Boulder.id)
            .order_by(desc(Boulder.rating))
        )
        .unique()
        .all()
    )

    return [
        BoulderWithAscentCount(
            id=boulder.id,
            name=boulder.name,
            grade=boulder.grade,
            slash_grade=boulder.slash_grade,
            rating=boulder.rating,
            number_of_rating=boulder.number_of_rating,
            url=boulder.url,
            area=boulder.area,
            styles=boulder.styles,
            ascents=ascents,
        )
        for boulder, ascents in result
    ]


def get_general_best_rated_boulders(db: Session):
    # Get all boulders with a rating above 4.6 and more than 8 recorded ratings
    boulders = (
        db.execute(
            select(Boulder, func.count(Ascent.user_id).label("ascents"))
            .join(Ascent, Ascent.boulder_id == Boulder.id)
            .options(
                joinedload(Boulder.area),
                joinedload(Boulder.grade),
                joinedload(Boulder.slash_grade),
                joinedload(Boulder.styles),
            )
            .where(and_(Boulder.rating >= 4.6, Boulder.number_of_rating >= 8))
            .group_by(Boulder.id)
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
                grade=boulder.grade,
                slash_grade=boulder.slash_grade,
                rating=boulder.rating,
                number_of_rating=boulder.number_of_rating,
                url=boulder.url,
                area=boulder.area,
                styles=boulder.styles,
                ascents=ascents,
            )
        )

    # Build final result
    result = [
        BoulderByGrade(grade=grade, boulders=result_map.get(grade.id, []))
        for grade in grades
    ]

    return result


# Most ascents boulders
def get_general_most_ascents_boulders_per_grade(db: Session, grade: str):
    result = (
        db.execute(
            select(Boulder, func.count(Ascent.user_id).label("ascents"))
            .join(Boulder.ascents)
            .join(Boulder.grade)
            .options(
                joinedload(Boulder.area),
                joinedload(Boulder.styles),
                joinedload(Boulder.grade),
                joinedload(Boulder.slash_grade),
            )
            .where(Grade.value == grade)
            .group_by(Ascent.boulder_id)
            .order_by(desc("ascents"))
            .limit(10)
        )
        .unique()
        .all()
    )

    return [
        BoulderWithAscentCount(
            id=boulder.id,
            name=boulder.name,
            grade=boulder.grade,
            slash_grade=boulder.slash_grade,
            rating=boulder.rating,
            number_of_rating=boulder.number_of_rating,
            url=boulder.url,
            area=boulder.area,
            styles=boulder.styles,
            ascents=ascents,
        )
        for boulder, ascents in result
    ]


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
                joinedload(Boulder.area),
                joinedload(Boulder.grade),
                joinedload(Boulder.slash_grade),
                joinedload(Boulder.styles),
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
                grade=boulder.grade,
                slash_grade=boulder.slash_grade,
                rating=boulder.rating,
                number_of_rating=boulder.number_of_rating,
                url=boulder.url,
                area=boulder.area,
                styles=boulder.styles,
                ascents=ascents,
            )
        )

    # Build final result
    result = [
        BoulderByGrade(grade=grade, boulders=result_map.get(grade.id, []))
        for grade in grades
    ]

    return result


# Hardest boulders
def get_general_hardest_boulders(db: Session, exclude_traverse: bool):
    query = select(Boulder)
    if exclude_traverse:
        subquery_traverse = (
            select(1)
            .select_from(boulder_style_table)
            .join(Style, Style.id == boulder_style_table.c.style_id)
            .where(
                and_(
                    Boulder.id == boulder_style_table.c.boulder_id,
                    Style.style.in_(
                        [
                            "traversée",
                            "traversée d-g",
                            "traversée g-d",
                            "boucle",
                        ]
                    ),
                )
            )
        )
        query = query.where(~exists(subquery_traverse))

    subquery = (
        select(Grade.correspondence)
        .where(Grade.value == "8c")
        .scalar_subquery()
    )

    query = (
        query.where(Grade.correspondence >= subquery)
        .join(Grade, Boulder.grade_id == Grade.id)
        .order_by(desc(Grade.correspondence), Boulder.name)
    )

    return db.scalars(query).all()


# Area based statistics
def get_areas_with_most_ascents(db: Session):
    result = db.execute(
        select(Area, func.count(Ascent.user_id).label("ascents_count"))
        .join(Boulder, Boulder.area_id == Area.id)
        .join(Ascent, Ascent.boulder_id == Boulder.id)
        .group_by(Area.id)
        .order_by(desc("ascents_count"))
        .limit(10)
    ).all()

    return [AreaCount(area=area, count=ascents) for area, ascents in result]


def get_areas_with_most_boulders(db: Session):
    result = db.execute(
        select(Area, func.count(Boulder.id).label("boulder_count"))
        .join(Boulder, Boulder.area_id == Area.id)
        .group_by(Area.id)
        .order_by(desc("boulder_count"))
        .limit(10)
    ).all()

    return [AreaCount(area=area, count=boulders) for area, boulders in result]


# Grade based statistics
def get_general_grade_distribution(db: Session):
    result = db.execute(
        select(Grade, func.count(Boulder.id))
        .join(Boulder, Boulder.grade_id == Grade.id)
        .group_by(Grade.correspondence)
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


# Style based statistics
def get_general_style_distribution(db: Session):
    result = db.execute(
        select(Style.style, func.count(Boulder.id).label("boulder_count"))
        .join(boulder_style_table, Style.id == boulder_style_table.c.style_id)
        .join(Boulder, Boulder.id == boulder_style_table.c.boulder_id)
        .group_by(Style.style)
        .order_by(desc("boulder_count"))
    ).all()

    return [
        StyleDistribution(styleType=style, boulders=boulder_count)
        for style, boulder_count in result
    ]


# User based statistics
def get_top_repeaters(db: Session):
    result = db.execute(
        select(User, func.count(Ascent.boulder_id).label("boulder_count"))
        .join(Ascent, User.id == Ascent.user_id)
        .group_by(User.id)
        .order_by(desc("boulder_count"))
        .limit(20)
    ).all()

    return [
        UserBoulderCount(
            id=user.id, username=user.username, boulder_count=boulder_count
        )
        for user, boulder_count in result
    ]


def get_top_setters(db: Session):
    result = db.execute(
        select(
            User,
            func.count(boulder_setter_table.c.boulder_id).label(
                "boulder_count"
            ),
        )
        .join(boulder_setter_table, User.id == boulder_setter_table.c.user_id)
        .group_by(User.id)
        .order_by(desc("boulder_count"))
        .limit(20)
    ).all()

    return [
        UserBoulderCount(
            id=user.id, username=user.username, boulder_count=boulder_count
        )
        for user, boulder_count in result
    ]


def get_ascents_volume_distribution(db: Session):
    # Subquery: count ascents per user
    user_counts = (
        select(
            Ascent.user_id,
            func.count(Ascent.boulder_id).label("repeat_count"),
        )
        .group_by(Ascent.user_id)
        .subquery()
    )

    # Categorize users by ascent count
    category_case = case(
        (user_counts.c.repeat_count < 20, "1–19"),
        (user_counts.c.repeat_count < 50, "20–49"),
        (user_counts.c.repeat_count < 100, "50–99"),
        (user_counts.c.repeat_count < 200, "100–199"),
        (user_counts.c.repeat_count < 500, "200–499"),
        (user_counts.c.repeat_count < 1000, "500–999"),
        else_="1000+",
    )

    # Final query: count users per range

    results = db.execute(
        select(category_case, func.count(category_case).label("count"))
        .group_by(category_case)
        .order_by(desc("count"))
    ).all()

    return [
        UserAscentVolume(group=group, number_of_users=count)
        for group, count in results
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
                    / cast(total_repeats, Float)
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
