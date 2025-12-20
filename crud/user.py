from sqlalchemy import and_, desc, func, select
from sqlalchemy.orm import Session
from models.area import Area
from models.boulder import Boulder
from models.grade import Grade
from models.ascent import Ascent
from models.user import User
from models.boulder_setter import boulder_setter_table
from schemas.area import AreaCount
from schemas.user import UserStats
from schemas.grade import GradeAscents


def get_all_users(
    db: Session, skip: int = 0, limit: int = 20, username: str = None
):
    query = select(User)
    if username:
        query = query.where(User.username.ilike(f"%{username}%"))
    return db.scalars(query.offset(skip).limit(limit))


def get_user(db: Session, id: int):
    return db.scalar(select(User).where(User.id == id))


def get_user_boulders_set(db: Session, user_id: int):
    return db.scalars(
        select(Boulder)
        .where(boulder_setter_table.c.user_id == user_id)
        .join(
            boulder_setter_table,
            Boulder.id == boulder_setter_table.c.boulder_id,
        )
    )


def get_user_boulders_repeated(db: Session, user_id: int):
    return db.scalars(
        select(Boulder)
        .where(Ascent.user_id == user_id)
        .join(Ascent, Boulder.id == Ascent.boulder_id)
    )


def get_username_from_id(db: Session, user_id: int):
    return db.scalar(select(User.username).where(User.id == user_id))


def get_number_of_ascents(db: Session, user_id: int):
    return db.scalar(
        select(func.count(Ascent.boulder_id)).where(Ascent.user_id == user_id)
    )


def get_user_average_grade(db: Session, user_id: int):
    subquery = (
        select(func.avg(Grade.correspondence))
        .where(and_(Ascent.user_id == user_id, Grade.value.is_not("P")))
        .join(Boulder, Boulder.grade_id == Grade.id)
        .join(Ascent, Ascent.boulder_id == Boulder.id)
    ).scalar_subquery()

    return db.scalar(
        select(Grade).where(Grade.correspondence == func.round(subquery))
    )


def get_user_hardest_grade(db: Session, user_id: int):
    return db.scalar(
        select(Grade)
        .where(Ascent.user_id == user_id)
        .join(Boulder, Boulder.grade_id == Grade.id)
        .join(Ascent, Ascent.boulder_id == Boulder.id)
        .order_by(desc(Grade.correspondence))
    )


def get_user_grade_distribution(db: Session, user_id: int):
    result = db.execute(
        select(Grade, func.count(Ascent.boulder_id))
        .where(Ascent.user_id == user_id)
        .join(Boulder, Boulder.grade_id == Grade.id)
        .join(Ascent, Ascent.boulder_id == Boulder.id)
        .group_by(Grade.value)
        .order_by(desc(Grade.correspondence)),
    ).all()

    return [
        GradeAscents(grade=grade, ascents=count) for grade, count in result
    ]


def get_user_area_distribution(db: Session, user_id: int):
    result = db.execute(
        select(
            Area,
            func.count(Ascent.boulder_id).label("number_of_ascents"),
        )
        .where(Ascent.user_id == user_id)
        .join(Boulder, Boulder.area_id == Area.id)
        .join(Ascent, Ascent.boulder_id == Boulder.id)
        .group_by(Area)
        .order_by(desc("number_of_ascents"))
    ).all()
    return [AreaCount(area=area, count=count) for area, count in result]


def get_user_stats(db: Session, user_id: int):
    username = get_username_from_id(db, user_id)
    ascents = get_number_of_ascents(db, user_id)
    grade_distribution = get_user_grade_distribution(db, user_id)
    average_grade = get_user_average_grade(db, user_id)
    hardest_grade = get_user_hardest_grade(db, user_id)
    area_distribution = get_user_area_distribution(db, user_id)

    return UserStats(
        username=username,
        ascents=ascents,
        grade_distribution=grade_distribution,
        average_grade=average_grade,
        hardest_grade=hardest_grade,
        area_distribution=area_distribution,
    )
