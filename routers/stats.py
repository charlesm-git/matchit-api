from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from crud.stats import (
    get_areas_with_most_boulders,
    get_general_best_rated_boulders,
    get_general_best_rated_boulders_per_grade,
    get_general_most_ascents_boulders,
    get_general_statistics_home_page,
    get_areas_with_most_ascents,
    get_general_most_ascents_boulders_per_grade,
    get_general_grade_distribution,
    get_general_ascents_per_grade,
    get_general_ascents_per_month,
    get_general_ascents_per_year,
)
from database import get_db_session
from schemas.area import AreaCount
from schemas.boulder import (
    Boulder,
    BoulderWithAscentCount,
    BoulderByGrade,
)
from schemas.general import GeneralStatistics
from schemas.grade import GradeDistribution, GradeAscents
from schemas.ascent import AscentsPerMonth, AscentsPerYear

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/general")
def read_general_statistics(
    db: Session = Depends(get_db_session),
) -> GeneralStatistics:
    return get_general_statistics_home_page(db=db)


@router.get("/boulder/best-rated/{grade}")
def read_general_best_rated_boulders_per_grade(
    db: Session = Depends(get_db_session), grade: str = None
) -> List[BoulderWithAscentCount]:
    if grade is None:
        raise HTTPException(status_code=422, detail="A grade must be provided")
    boulders = get_general_best_rated_boulders_per_grade(db=db, grade=grade)
    return boulders


@router.get("/boulder/best-rated")
def read_general_best_rated_boulders(
    db: Session = Depends(get_db_session),
) -> List[BoulderByGrade]:
    boulders = get_general_best_rated_boulders(db=db)
    return boulders


@router.get("/boulder/most-ascents/{grade}")
def read_general_most_ascents_boulders_per_grade(
    db: Session = Depends(get_db_session), grade: str = None
) -> List[BoulderWithAscentCount]:
    if grade is None:
        raise HTTPException(status_code=422, detail="A grade must be provided")
    boulders = get_general_most_ascents_boulders_per_grade(db=db, grade=grade)
    return boulders


@router.get("/boulder/most-ascents")
def read_general_most_ascents_boulders(
    db: Session = Depends(get_db_session),
) -> List[BoulderByGrade]:
    boulders = get_general_most_ascents_boulders(db=db)
    return boulders


@router.get("/area/most-ascents")
def read_general_most_ascents_areas(
    db: Session = Depends(get_db_session),
) -> List[AreaCount]:
    boulders = get_areas_with_most_ascents(db=db)
    return boulders


@router.get("/area/most-boulders")
def read_general_most_boulders_areas(
    db: Session = Depends(get_db_session),
) -> List[AreaCount]:
    boulders = get_areas_with_most_boulders(db=db)
    return boulders


@router.get("/grade/distribution")
def read_general_grade_distribution(
    db: Session = Depends(get_db_session),
) -> List[GradeDistribution]:
    boulders = get_general_grade_distribution(db=db)
    return boulders


@router.get("/grade/ascent")
def read_general_ascents_per_grade(
    db: Session = Depends(get_db_session),
) -> List[GradeAscents]:
    grades = get_general_ascents_per_grade(db=db)
    return grades


@router.get("/time/ascent/per-month")
def read_general_repeats_per_month(
    db: Session = Depends(get_db_session), grade: str = None
) -> List[AscentsPerMonth]:
    ascents = get_general_ascents_per_month(db=db, grade=grade)
    return ascents


@router.get("/time/ascent/per-year")
def read_general_repeats_per_year(
    db: Session = Depends(get_db_session), grade: str = None
) -> List[AscentsPerYear]:
    ascents = get_general_ascents_per_year(db=db, grade=grade)
    return ascents
