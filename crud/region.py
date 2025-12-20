from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from models.area import Area
from models.region import Region


def get_all_regions(db: Session):
    return db.scalars(
        select(Region).options(joinedload(Region.areas))
    ).unique()


def get_areas_from_region(db: Session, region_id: int):
    return db.scalars(select(Area).where(Area.region_id == region_id))
