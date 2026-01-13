from typing import List
from pydantic import BaseModel


class SearchOutput(BaseModel):
    boulders: List["BoulderWithAscentCount"]
    areas: List["Area"]
    crags: List["Crag"]

    class Config:
        from_attributes = True


from schemas.boulder import BoulderWithAscentCount
from schemas.area import Area
from schemas.crag import Crag
