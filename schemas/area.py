from __future__ import annotations

from typing import List, Union
from pydantic import BaseModel


class Area(BaseModel):
    id: int
    name: str
    name_normalized: str
    slug: str
    external_slug: str
    url: str
    country_id: int

    class Config:
        from_attributes = True


class AreaDetail(BaseModel):
    id: int
    name: str
    name_normalized: str
    slug: str
    external_slug: str
    url: str
    crags: List["Crag"]

    class Config:
        from_attributes = True


class AreaStats(BaseModel):
    area: "AreaDetail"
    number_of_boulders: int
    average_grade: Union["Grade", None]
    ascents: int
    grade_distribution: List["GradeDistribution"]
    most_climbed_boulders: List["BoulderWithAscentCount"]
    best_rated_boulders: List["BoulderWithAscentCount"]

    class Config:
        from_attributes = True


class AreaCount(BaseModel):
    area: Area
    count: int

    class Config:
        from_attributes = True


from schemas.grade import Grade, GradeDistribution
from schemas.crag import Crag
from schemas.boulder import BoulderWithAscentCount
