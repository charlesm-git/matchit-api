from functools import lru_cache

from scipy.sparse import load_npz
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models import ascent


DB_PATH = "matchit.db"

DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DATABASE_URL, echo=False)

MONTH_LIST = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


def get_db_session():
    with Session(engine) as session:
        yield session
