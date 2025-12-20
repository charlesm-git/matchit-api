from functools import lru_cache

from scipy.sparse import load_npz
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models import ascent


DB_PATH = "bleau_info_stats.db"

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


@lru_cache(maxsize=1)
def get_recommendation_matrices():
    """Dependency that return the cached recommendation matrices"""
    print("Matrices loading...")
    ascents = load_npz("./similarity_ascent.npz")
    style = load_npz("./similarity_style.npz")
    grade = load_npz("./similarity_grade.npz")
    print("Matrices loaded successfully")
    return (ascents, style, grade)
