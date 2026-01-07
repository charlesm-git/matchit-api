from typing import List
from pydantic import BaseModel

from schemas.grade import Grade, GradeAscents
from schemas.area import AreaCount


class User(BaseModel):
    id: int
    name: str
    url: str | None = None

    class Config:
        from_attributes = True

class UserBoulderCount(User):
    boulder_count: int


class UserAscentVolume(BaseModel):
    group: str
    number_of_users: int

    class Config:
        from_attributes = True
