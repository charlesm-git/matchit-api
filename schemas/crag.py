from __future__ import annotations

from typing import List, Union
from pydantic import BaseModel


class Crag(BaseModel):
    id: int
    name: str
    name_normalized: str
    area_id: int
    slug: str
    url: str
    is_synthetic: bool

    class Config:
        from_attributes = True


class CragWithArea(BaseModel):
    id: int
    name: str
    name_normalized: str
    slug: str
    url: str
    is_synthetic: bool
    area: Area

    class Config:
        from_attributes = True


class CragWithCounts(BaseModel):
    id: int
    name: str
    name_normalized: str
    slug: str
    url: str
    is_synthetic: bool
    boulder_count: int
    ascent_count: int

    class Config:
        from_attributes = True


class CragStats(BaseModel):
    crag: CragWithArea
    number_of_boulders: int
    average_grade: Union["Grade", None]
    ascents: int
    grade_distribution: List["GradeDistribution"]
    most_climbed_boulders: List["BoulderWithAscentCount"]
    best_rated_boulders: List["BoulderWithAscentCount"]


from schemas.area import Area
from schemas.grade import Grade, GradeDistribution
from schemas.boulder import BoulderWithAscentCount
