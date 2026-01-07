from __future__ import annotations

from typing import List
from pydantic import BaseModel


class RecommendationRequest(BaseModel):
    boulder_ids: List[int]
    top_N: int = 10
