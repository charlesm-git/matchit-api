from typing import List
from pydantic import BaseModel

from schemas.grade import Grade, GradeAscents
from schemas.area import AreaCount


class User(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


class UserDetail(User):
    url: str


class UserStats(BaseModel):
    username: str
    ascents: int
    average_grade: Grade
    hardest_grade: Grade
    grade_distribution: List[GradeAscents]
    area_distribution: List[AreaCount]

    class Config:
        from_attributes = True


class UserBoulderCount(User):
    boulder_count: int


class UserAscentVolume(BaseModel):
    group: str
    number_of_users: int

    class Config:
        from_attributes = True
