from __future__ import annotations

from typing import List, Union
from pydantic import BaseModel


class Boulder(BaseModel):
    id: int
    name: str
    rating: float | None = None
    number_of_rating: int = 0
    url: str

    class Config:
        from_attributes = True


class BoulderWithFullDetail(Boulder):
    grade: "Grade"
    slash_grade: Union["Grade", None] = None
    area: "Area"
    styles: List["Style"] = []
    ascents: List["AscentRead"] = []
    aggregated_ascents: List["AscentsPerMonthWithGeneral"] = []



class BoulderWithAscentCount(Boulder):
    grade: "Grade"
    slash_grade: Union["Grade", None] = None
    area: Area
    styles: List["Style"] = []
    ascents: int
    
    @classmethod
    def from_query_result(cls, boulder, ascent_count):
        return cls.model_validate({**boulder.__dict__, "ascents": ascent_count})


class BoulderByGrade(BaseModel):
    grade: "Grade"
    boulders: List["BoulderWithAscentCount"]


from schemas.area import Area
from schemas.grade import Grade
from schemas.ascent import AscentRead, AscentsPerMonthWithGeneral
from schemas.style import Style
