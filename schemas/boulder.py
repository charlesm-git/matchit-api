from __future__ import annotations

from typing import List
from pydantic import BaseModel


class Boulder(BaseModel):
    id: int
    name: str
    name_normalized: str
    rating: float | None = None
    url: str
    slug: str

    class Config:
        from_attributes = True


class BoulderWithFullDetail(Boulder):
    grade: "Grade"
    crag: "Crag"
    area: "Area"
    ascents: List["AscentRead"] = []
    aggregated_ascents: List["AscentsPerMonthWithGeneral"] = []


class BoulderWithAscentCount(Boulder):
    grade: "Grade"
    crag: "Crag"
    area: "Area"
    ascents: int

    @classmethod
    def from_query_result(cls, boulder, ascent_count):
        return cls.model_validate(
            {
                **boulder.__dict__,
                "area": boulder.crag.area,
                "ascents": ascent_count,
            }
        )


class RecommendationOutput(BoulderWithAscentCount):
    score: float


class BoulderByGrade(BaseModel):
    grade: "Grade"
    boulders: List["BoulderWithAscentCount"]


from schemas.crag import Crag
from schemas.area import Area
from schemas.grade import Grade
from schemas.ascent import AscentRead, AscentsPerMonthWithGeneral

BoulderWithFullDetail.model_rebuild()
BoulderWithAscentCount.model_rebuild()
BoulderByGrade.model_rebuild()
