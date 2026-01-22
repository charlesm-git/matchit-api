from collections import defaultdict
from typing import List, Dict, Set, Tuple

from sqlalchemy import and_, not_, or_, select
from sqlalchemy.orm import selectinload
from rapidfuzz import fuzz

from database import Session
from models.boulder import Boulder
from models.crag import Crag
from models.grade import Grade


def get_boulders_for_duplicate_check(
    db: Session, area_slug: str = None
) -> List[Boulder]:
    """Fetch boulders from the database for duplicate checking."""
    query = (
        select(Boulder)
        .options(
            selectinload(Boulder.crag),
            selectinload(Boulder.grade),
            selectinload(Boulder.ascents),
        )
        .join(Boulder.grade)
        .where(
            and_(
                Boulder.ascents.any(),
                Boulder.main_boulder_id.is_(None),
                not_(
                    or_(
                        Boulder.name_normalized.ilike("%n.n.%"),
                        Boulder.name_normalized.ilike("%n n%"),
                    )
                ),
            )
        )
        .order_by(Grade.correspondence)
    )  # Only boulders with ascents

    # Filter by area if specified
    if area_slug:
        query = (
            query.join(Boulder.crag)
            .join(Crag.area)
            .where(Crag.area.has(slug=area_slug))
        )

    boulders = db.scalars(query).unique().all()
    return boulders


def calculate_similarity(
    name1: str, name2: str, algorithm: str = "ratio"
) -> float:
    """
    Calculate similarity between two names using specified algorithm.

    Args:
        name1: First name
        name2: Second name
        algorithm: One of 'ratio', 'token_sort'

    Returns:
        Similarity score (0-100)
    """
    if algorithm == "ratio":
        return fuzz.ratio(name1, name2)
    elif algorithm == "token_sort":
        return fuzz.token_sort_ratio(name1, name2)
    else:
        return fuzz.ratio(name1, name2)


def find_duplicate_groups(
    db: Session,
    min_similarity: int = 85,
    grade_tolerance: int = 2,
    area_slug: str = None,
    algorithm: str = "ratio",
    group_by_crag: bool = True,
    detect_overlaps: bool = True,
) -> Dict:
    """
    Find groups of potentially duplicate boulders using graph-based clustering.

    Args:
        db: Database session
        min_similarity: Minimum similarity score (0-100) for names to be considered duplicates
        grade_tolerance: Max grade value difference to consider boulders as potential duplicates
        area_slug: Optional area slug to limit search to specific area
        algorithm: Similarity algorithm ('ratio' or 'token_sort')
        group_by_crag: If True, only compare boulders within the same crag
        detect_overlaps: If True, return metadata about overlapping groups

    Returns:
        Dict with 'groups' (list of boulder groups) and 'overlaps' (boulder IDs appearing in multiple groups)
    """
    boulders = get_boulders_for_duplicate_check(db, area_slug=area_slug)

    # Build similarity graph: {boulder_id: {similar_boulder_id: similarity_score}}
    similarity_graph = defaultdict(dict)
    boulder_map = {b.id: b for b in boulders}

    if group_by_crag:
        boulders_by_crag = defaultdict(list)
        for boulder in boulders:
            boulders_by_crag[boulder.crag_id].append(boulder)

        for crag_id, crag_boulders in boulders_by_crag.items():
            if len(crag_boulders) < 2:
                continue
            crag_boulders.sort(key=lambda b: b.grade.correspondence)
            _build_similarity_graph(
                crag_boulders,
                similarity_graph,
                min_similarity,
                grade_tolerance,
                algorithm,
            )
    else:
        boulders.sort(key=lambda b: b.grade.correspondence)
        _build_similarity_graph(
            boulders,
            similarity_graph,
            min_similarity,
            grade_tolerance,
            algorithm,
        )

    # Use connected components to find groups
    groups = _find_connected_components(similarity_graph, boulder_map)

    # Detect overlaps if requested
    overlaps = set()
    if detect_overlaps:
        boulder_occurrences = defaultdict(int)
        for group in groups:
            for boulder in group:
                boulder_occurrences[boulder.id] += 1
        overlaps = {
            bid for bid, count in boulder_occurrences.items() if count > 1
        }

    return {"groups": groups, "overlaps": list(overlaps)}


def _build_similarity_graph(
    boulders: List[Boulder],
    similarity_graph: Dict,
    min_similarity: int,
    grade_tolerance: int,
    algorithm: str,
):
    """Build similarity edges in the graph."""
    for i, boulder1 in enumerate(boulders):
        for boulder2 in boulders[i + 1 :]:
            grade_diff = abs(
                boulder1.grade.correspondence - boulder2.grade.correspondence
            )
            # Skip if grade difference exceeds tolerance
            if grade_diff > grade_tolerance:
                # Since list is sorted by grade, we can break early
                if (
                    boulder2.grade.correspondence
                    > boulder1.grade.correspondence + grade_tolerance
                ):
                    break
                continue

            similarity = calculate_similarity(
                boulder1.name_normalized.lower(),
                boulder2.name_normalized.lower(),
                algorithm=algorithm,
            )

            if similarity >= min_similarity:
                similarity_graph[boulder1.id][boulder2.id] = similarity
                similarity_graph[boulder2.id][boulder1.id] = similarity


def _find_connected_components(
    similarity_graph: Dict, boulder_map: Dict[int, Boulder]
) -> List[List[Boulder]]:
    """Find quasi-clique clusters where members must be similar to majority of group."""
    MIN_GROUP_SIMILARITY = 0.5  # Member must be similar to 50% of group

    # Sort all boulders by ascent count (highest first) to seed groups with popular boulders
    sorted_boulder_ids = sorted(
        similarity_graph.keys(),
        key=lambda bid: len(boulder_map[bid].ascents),
        reverse=True,
    )

    assigned = set()
    components = []

    for seed_id in sorted_boulder_ids:
        if seed_id in assigned:
            continue

        # Start new group with seed boulder
        group = [seed_id]
        assigned.add(seed_id)

        # Try to add other unassigned boulders
        for candidate_id in sorted_boulder_ids:
            if candidate_id in assigned:
                continue

            # Count how many current group members the candidate is similar to
            similar_to_count = sum(
                1
                for group_id in group
                if candidate_id in similarity_graph.get(group_id, {})
            )

            # Require similarity to at least MIN_GROUP_SIMILARITY of group
            required_matches = max(1, int(len(group) * MIN_GROUP_SIMILARITY))

            if similar_to_count >= required_matches:
                group.append(candidate_id)
                assigned.add(candidate_id)

        # Only keep groups with 2+ members
        if len(group) > 1:
            boulder_group = [boulder_map[bid] for bid in group]
            # Already sorted by ascent count from initial sort
            components.append(boulder_group)

    return components


def find_single_boulder_duplicates(
    db: Session,
    boulder_id: int,
    min_similarity: int = 70,
    grade_tolerance: int = 3,
    algorithm: str = "token_sort",
    max_results: int = 20,
) -> List[Tuple[Boulder, float]]:
    """
    Find potential duplicates for a specific boulder with lower similarity threshold.

    Args:
        db: Database session
        boulder_id: ID of the boulder to find duplicates for
        min_similarity: Minimum similarity score (default lower for manual review)
        grade_tolerance: Max grade difference
        algorithm: Similarity algorithm
        max_results: Maximum number of results to return

    Returns:
        List of tuples (boulder, similarity_score) sorted by similarity descending
    """
    # Get the target boulder
    target = db.scalar(
        select(Boulder)
        .options(
            selectinload(Boulder.crag),
            selectinload(Boulder.grade),
            selectinload(Boulder.ascents),
        )
        .where(Boulder.id == boulder_id)
    )

    if not target:
        return []

    # Get candidate boulders in the same area with similar grades
    candidates = db.scalars(
        select(Boulder)
        .options(
            selectinload(Boulder.crag),
            selectinload(Boulder.grade),
            selectinload(Boulder.ascents),
        )
        .join(Boulder.grade)
        .join(Boulder.crag)
        .where(
            and_(
                Boulder.id != boulder_id,
                Boulder.main_boulder_id.is_(
                    None
                ),  # Not already marked as duplicate
                Grade.correspondence.between(
                    target.grade.correspondence - grade_tolerance,
                    target.grade.correspondence + grade_tolerance,
                ),
            )
        )
    ).all()

    # Calculate similarities
    results = []
    for candidate in candidates:
        similarity = calculate_similarity(
            target.name_normalized.lower(),
            candidate.name_normalized.lower(),
            algorithm=algorithm,
        )
        if similarity >= min_similarity:
            results.append((candidate, similarity))

    # Sort by similarity descending
    results.sort(key=lambda x: x[1], reverse=True)

    return results[:max_results]


def deduplicate_boulders(db: Session, target: int, duplicates: List[int]):
    """
    Deduplicate boulders by setting their main_boulder_id to the target boulder.
    Also cascades: any boulders pointing to these duplicates are redirected to the target.
    """
    duplicates_boulders = db.scalars(
        select(Boulder).where(Boulder.id.in_(duplicates))
    ).all()

    # Set duplicates to point to target
    for boulder in duplicates_boulders:
        boulder.main_boulder_id = target
        db.add(boulder)

    # Cascade: find any boulders that point to these duplicates and redirect to target
    cascade_boulders = db.scalars(
        select(Boulder).where(Boulder.main_boulder_id.in_(duplicates))
    ).all()

    for boulder in cascade_boulders:
        boulder.main_boulder_id = target
        db.add(boulder)

    db.commit()
    return duplicates_boulders


def get_existing_duplicates(db: Session, boulder_id: int) -> List[Boulder]:
    """
    Get all boulders currently marked as duplicates of the given boulder.

    Args:
        db: Database session
        boulder_id: ID of the main boulder

    Returns:
        List of boulders marked as duplicates
    """
    duplicates = db.scalars(
        select(Boulder)
        .options(
            selectinload(Boulder.crag),
            selectinload(Boulder.grade),
            selectinload(Boulder.ascents),
        )
        .where(Boulder.main_boulder_id == boulder_id)
    ).all()

    return duplicates


def remove_duplicate_relationship(db: Session, boulder_id: int) -> Boulder:
    """
    Remove the duplicate relationship for a boulder (unmark as duplicate).

    Args:
        db: Database session
        boulder_id: ID of the boulder to unmark

    Returns:
        The updated boulder
    """
    boulder = db.scalar(select(Boulder).where(Boulder.id == boulder_id))
    if boulder:
        boulder.main_boulder_id = None
        db.add(boulder)
        db.commit()
        db.refresh(boulder)
    return boulder


def move_ascents(db, source_boulder: Boulder, target_boulder: Boulder):
    """Move all ascents from source boulder to target boulder."""
    for ascent in source_boulder.ascents:
        ascent.boulder_id = target_boulder.id
        db.add(ascent)
    db.commit()
