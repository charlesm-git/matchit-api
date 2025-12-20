from __future__ import annotations

from pydantic import BaseModel


class GeneralStatistics(BaseModel):
    boulder_count: int
    area_count: int
    ascent_count: int
    average_grade: Grade

    class Config:
        from_attributes = True


from schemas.grade import Grade
