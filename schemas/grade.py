from pydantic import BaseModel


class Grade(BaseModel):
    id: int
    value: str
    correspondence: int
    eightanu_correspondence: int

    class Config:
        from_attributes = True


class GradeDistribution(BaseModel):
    grade: Grade
    boulders: int

    class Config:
        from_attributes = True


class GradeAscents(BaseModel):
    grade: Grade
    ascents: int

    class Config:
        from_attributes = True
