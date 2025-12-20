from typing import List
from pydantic import BaseModel


class SearchBoulderArea(BaseModel):
    boulders: List["BoulderWithAscentCount"]
    areas: List["Area"]

    class Config:
        from_attributes = True


from schemas.boulder import BoulderWithAscentCount
from schemas.area import Area
