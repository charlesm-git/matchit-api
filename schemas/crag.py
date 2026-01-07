from typing import List
from pydantic import BaseModel

from schemas.area import Area


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
