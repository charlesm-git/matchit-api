from __future__ import annotations

from typing import List
from pydantic import BaseModel


class RecommendationRequest(BaseModel):
    boulder_ids: List[int]
    ascent_weight: float = 0.6
    style_weight: float = 0.2
    grade_weight: float = 0.2
    top_N: int = 10
