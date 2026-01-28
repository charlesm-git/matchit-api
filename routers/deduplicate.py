from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from crud.deduplicate import (
    deduplicate_boulders,
    delete_duplicate_relationship,
    find_duplicate_groups,
    find_single_boulder_duplicates,
    get_existing_duplicates,
    move_ascents,
)
from database import get_db_session
from dependencies import get_current_account
from models.account import Account
from models.boulder import Boulder
from schemas.deduplicate import (
    BatchMergeRequest,
    BatchMergeResponse,
    BoulderDuplicateInfo,
    DuplicateGroup,
    BatchDuplicateParams,
    BatchDuplicateResponse,
    MergeOperation,
    MergeResult,
    MoveAscentsResponse,
    RemoveDuplicateRequest,
    RemoveDuplicateResponse,
    SingleBoulderDuplicateParams,
    SingleBoulderDuplicatesResponse,
)

router = APIRouter(prefix="/deduplicate", tags=["deduplicate"])


def _boulder_to_duplicate_info(
    boulder: Boulder,
    similarity_score=None,
):
    """Convert Boulder model to BoulderDuplicateInfo schema."""
    return BoulderDuplicateInfo(
        id=boulder.id,
        name=boulder.name,
        name_normalized=boulder.name_normalized,
        grade_value=boulder.grade.value,
        grade_correspondence=boulder.grade.correspondence,
        crag_name=boulder.crag.name,
        ascent_count=len(boulder.ascents),
        similarity_score=similarity_score,
    )


@router.post("/batch")
def get_duplicate_groups(
    params: BatchDuplicateParams,
    db: Session = Depends(get_db_session),
    account: Account = Depends(get_current_account),
) -> BatchDuplicateResponse:
    """
    Find groups of potential duplicate boulders based on similarity and grade.

    This uses graph-based clustering to identify connected components of similar boulders.
    The response includes any overlapping boulder IDs that appear in multiple groups.
    """
    result = find_duplicate_groups(
        db=db,
        min_similarity=params.min_similarity,
        grade_tolerance=params.grade_tolerance,
        area_slug=params.area_slug,
        algorithm=params.algorithm,
        group_by_crag=params.group_by_crag,
        detect_overlaps=True,
    )

    groups = []
    overlapping_ids = set(result["overlaps"])

    for boulder_group in result["groups"]:
        # Convert to schema objects
        boulder_infos = [_boulder_to_duplicate_info(b) for b in boulder_group]

        # Check if any boulder in this group is in multiple groups
        has_conflicts = any(b.id in overlapping_ids for b in boulder_group)

        groups.append(
            DuplicateGroup(
                boulders=boulder_infos,
                has_conflicts=has_conflicts,
            )
        )

    return BatchDuplicateResponse(
        groups=groups,
        total_groups=len(groups),
        overlapping_boulder_ids=list(overlapping_ids),
    )


@router.post("/batch/merge")
def merge_duplicate_groups(
    request: BatchMergeRequest,
    db: Session = Depends(get_db_session),
    account: Account = Depends(get_current_account),
) -> BatchMergeResponse:
    """
    Batch merge multiple duplicate groups in a single operation.

    Each merge operation specifies:
    - target_boulder_id: The main boulder to keep
    - duplicate_boulder_ids: Boulders to mark as duplicates of the target
    - ignore_boulder_ids: Boulders to skip (leave unchanged)
    """
    results = []
    successful = 0
    failed = 0

    for merge_op in request.merges:
        try:
            # Validate target exists
            target = db.scalar(
                select(Boulder).where(Boulder.id == merge_op.target_boulder_id)
            )
            if not target:
                results.append(
                    MergeResult(
                        target_boulder_id=merge_op.target_boulder_id,
                        merged_count=0,
                        success=False,
                        error=f"Target boulder {merge_op.target_boulder_id} not found",
                    )
                )
                failed += 1
                continue

            # Mark duplicates
            merged = deduplicate_boulders(
                db=db,
                target=merge_op.target_boulder_id,
                duplicates=merge_op.duplicate_boulder_ids,
            )

            results.append(
                MergeResult(
                    target_boulder_id=merge_op.target_boulder_id,
                    merged_count=len(merged),
                    success=True,
                )
            )
            successful += 1

        except Exception as e:
            results.append(
                MergeResult(
                    target_boulder_id=merge_op.target_boulder_id,
                    merged_count=0,
                    success=False,
                    error=str(e),
                )
            )
            failed += 1

    return BatchMergeResponse(
        results=results,
        total_operations=len(request.merges),
        successful=successful,
        failed=failed,
        message=f"Processed {len(request.merges)} merge operations: {successful} successful, {failed} failed",
    )


@router.post("/boulder/merge")
def merge_single_boulder_duplicates(
    request: MergeOperation,
    db: Session = Depends(get_db_session),
    account: Account = Depends(get_current_account),
) -> MergeResult:
    """
    Merge selected boulders into a target boulder (single boulder workflow).
    """
    target = db.scalar(
        select(Boulder).where(Boulder.id == request.target_boulder_id)
    )
    if not target:
        raise HTTPException(status_code=404, detail="Target boulder not found")

    merged = deduplicate_boulders(
        db=db,
        target=request.target_boulder_id,
        duplicates=request.duplicate_boulder_ids,
    )

    return MergeResult(
        target_boulder_id=request.target_boulder_id,
        merged_count=len(merged),
        success=True,
    )


@router.post(
    "/boulder/delete-duplicates",
)
def remove_duplicate_relationship_endpoint(
    request: RemoveDuplicateRequest,
    db: Session = Depends(get_db_session),
    account: Account = Depends(get_current_account),
) -> RemoveDuplicateResponse:
    """
    Remove the duplicate relationship for a boulder (unmark it as a duplicate).

    This sets main_boulder_id back to NULL, restoring the boulder as an independent entry.
    """
    delete_duplicate_relationship(db=db, boulder_ids=request.boulder_ids)

    return RemoveDuplicateResponse(
        boulder_ids=request.boulder_ids,
        message=f"Successfully removed duplicate relationship for boulders {request.boulder_ids}",
    )


@router.post(
    "/boulder/{boulder_id}",
)
def get_single_boulder_duplicates(
    boulder_id: int,
    params: SingleBoulderDuplicateParams,
    db: Session = Depends(get_db_session),
    account: Account = Depends(get_current_account),
) -> SingleBoulderDuplicatesResponse:
    """
    Find potential duplicates for a specific boulder using a lower similarity threshold.

    Also returns existing boulders already marked as duplicates of this boulder.
    """
    # Validate boulder exists
    target = db.scalar(select(Boulder).where(Boulder.id == boulder_id))
    if not target:
        raise HTTPException(status_code=404, detail="Boulder not found")

    # Find potential duplicates
    candidates = find_single_boulder_duplicates(
        db=db,
        boulder_id=boulder_id,
        min_similarity=params.min_similarity,
        grade_tolerance=params.grade_tolerance,
        algorithm=params.algorithm,
        max_results=params.max_results,
    )

    # Get existing duplicates
    existing = get_existing_duplicates(db=db, boulder_id=boulder_id)

    candidate_infos = [
        _boulder_to_duplicate_info(boulder, similarity)
        for boulder, similarity in candidates
    ]

    existing_infos = [_boulder_to_duplicate_info(b) for b in existing]

    return SingleBoulderDuplicatesResponse(
        boulder_id=boulder_id,
        boulder_name=target.name,
        candidates=candidate_infos,
        existing_duplicates=existing_infos,
    )


@router.get("/move-ascents")
def move_ascents_for_all_duplicates(
    db: Session = Depends(get_db_session),
    account: Account = Depends(get_current_account),
) -> MoveAscentsResponse:
    """
    Move ascents from duplicate boulders to their main boulders for all duplicates in the database.
    """
    result = move_ascents(db=db)
    return result
