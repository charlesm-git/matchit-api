from datetime import date
from pydantic import BaseModel


class Ascent(BaseModel):
    boulder_id: int
    user_id: int
    log_grade_id: int
    log_date: date
    type: str
    rating: int
    
    with_kneepad: bool
    is_fa: bool
    is_soft: bool
    is_hard: bool
    is_repeat: bool
    is_overhang: bool
    is_vertical: bool
    is_slab: bool
    is_roof: bool
    is_athletic: bool
    is_endurance: bool
    is_crimpy: bool
    is_cruxy: bool
    is_sloper: bool
    is_technical: bool
    recommended: bool
    

    class Config:
        from_attributes = True


class AscentRead(BaseModel):
    user: "User"
    log_date: date
    log_grade: "Grade"
    type: str | None = None
    rating: int
    
    with_kneepad: bool
    is_fa: bool
    is_soft: bool
    is_hard: bool
    is_repeat: bool
    is_overhang: bool
    is_vertical: bool
    is_slab: bool
    is_roof: bool
    is_athletic: bool
    is_endurance: bool
    is_crimpy: bool
    is_cruxy: bool
    is_sloper: bool
    is_technical: bool
    recommended: bool

    class Config:
        from_attributes = True


class AscentsPerMonth(BaseModel):
    month: str
    percentage: float

    class Config:
        from_attributes = True


class AscentsPerMonthWithGeneral(BaseModel):
    month: str
    boulder: float
    general: float

    class Config:
        from_attributes = True


class AscentsPerYear(BaseModel):
    year: str
    ascents: int

    class Config:
        from_attributes = True

from models.grade import Grade
from schemas.user import User