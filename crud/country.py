from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from models.country import Country


def get_countries(db: Session):
    return db.scalars(select(Country).order_by(Country.name)).all()


def get_all_countries_with_areas(db: Session, limit: int = None):
    return (
        db.scalars(
            select(Country)
            .options(joinedload(Country.areas))
            .order_by(Country.name)
            .limit(limit)
        )
        .unique()
        .all()
    )
