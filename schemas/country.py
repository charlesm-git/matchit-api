from __future__ import annotations

from typing import List, Union
from pydantic import BaseModel


class Country(BaseModel):
    id: int
    name: str
    name_normalized: str
    slug: str

    class Config:
        from_attributes = True


class CountryDetail(BaseModel):
    id: int
    name: str
    name_normalized: str
    slug: str
    areas: List["Area"]

    class Config:
        from_attributes = True


from schemas.crag import Crag
from schemas.area import Area
