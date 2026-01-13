from pydantic import BaseModel


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
