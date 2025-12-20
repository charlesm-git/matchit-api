from typing import List
from pydantic import BaseModel

from schemas.area import Area


class Region(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class RegionDetail(BaseModel):
    id: int
    name: str
    areas: List[Area]

    class Config:
        from_attributes = True
