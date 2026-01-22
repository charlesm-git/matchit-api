from typing import List, Optional
from pydantic import BaseModel, Field


class DuplicateGroupParams(BaseModel):
    """Parameters for finding duplicate groups."""

    area_slug: Optional[str] = None
    min_similarity: int = Field(default=85, ge=0, le=100)
    grade_tolerance: int = Field(default=2, ge=0, le=10)
    algorithm: str = Field(default="ratio", pattern="^(ratio|token_sort)$")
    group_by_crag: bool = True


class BoulderDuplicateInfo(BaseModel):
    """Boulder info for duplicate detection."""

    id: int
    name: str
    name_normalized: str
    grade_value: str
    grade_correspondence: int
    crag_name: str
    ascent_count: int
    similarity_score: Optional[float] = None

    class Config:
        from_attributes = True


class DuplicateGroup(BaseModel):
    """A group of potential duplicate boulders."""

    boulders: List[BoulderDuplicateInfo]
    has_conflicts: bool = False


class DuplicateGroupsResponse(BaseModel):
    """Response containing all duplicate groups."""

    groups: List[DuplicateGroup]
    total_groups: int
    overlapping_boulder_ids: List[int] = []


class MergeOperation(BaseModel):
    """Single merge operation for batch processing."""

    target_boulder_id: int
    duplicate_boulder_ids: List[int]
    ignore_boulder_ids: Optional[List[int]] = []


class BatchMergeRequest(BaseModel):
    """Request to merge multiple groups in batch."""

    merges: List[MergeOperation]


class MergeResult(BaseModel):
    """Result of a single merge operation."""

    target_boulder_id: int
    merged_count: int
    ignored_count: int
    success: bool
    error: Optional[str] = None


class BatchMergeResponse(BaseModel):
    """Response after batch merging groups."""

    results: List[MergeResult]
    total_operations: int
    successful: int
    failed: int
    message: str


class SingleBoulderDuplicateParams(BaseModel):
    """Parameters for finding duplicates of a single boulder."""

    min_similarity: int = Field(default=70, ge=0, le=100)
    grade_tolerance: int = Field(default=3, ge=0, le=10)
    algorithm: str = Field(
        default="token_sort", pattern="^(ratio|token_sort)$"
    )
    max_results: int = Field(default=20, ge=1, le=100)


class SingleBoulderDuplicatesResponse(BaseModel):
    """Response with potential duplicates for a single boulder."""

    boulder_id: int
    boulder_name: str
    candidates: List[BoulderDuplicateInfo]
    existing_duplicates: List[BoulderDuplicateInfo]


class MergeSingleRequest(BaseModel):
    """Request to merge specific boulders to a target."""

    target_boulder_id: int
    duplicate_boulder_ids: List[int]


class RemoveDuplicateRequest(BaseModel):
    """Request to remove duplicate relationship."""

    boulder_id: int


class RemoveDuplicateResponse(BaseModel):
    """Response after removing duplicate relationship."""

    boulder_id: int
    message: str
