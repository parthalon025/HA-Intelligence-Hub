"""Validate organic clusters against seed (hard-coded) capabilities."""
import logging

logger = logging.getLogger(__name__)

MATCH_THRESHOLD = 0.8


def jaccard_similarity(set_a: set, set_b: set) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def validate_seeds(
    seed_capabilities: dict,
    clusters: list[dict],
    threshold: float = MATCH_THRESHOLD,
) -> dict:
    """Compare discovered clusters against seed capabilities.

    Returns dict mapping seed name to validation result:
        best_jaccard, best_cluster_id, matched (bool)
    """
    results = {}

    for seed_name, seed_data in seed_capabilities.items():
        seed_entities = set(seed_data.get("entities", []))
        best_jaccard = 0.0
        best_cluster_id = None

        for cluster in clusters:
            cluster_entities = set(cluster["entity_ids"])
            sim = jaccard_similarity(seed_entities, cluster_entities)
            if sim > best_jaccard:
                best_jaccard = sim
                best_cluster_id = cluster["cluster_id"]

        matched = best_jaccard >= threshold
        if not matched and seed_entities:
            logger.warning(
                f"Seed '{seed_name}' not reproduced: best Jaccard={best_jaccard:.2f} "
                f"(threshold={threshold})"
            )

        results[seed_name] = {
            "best_jaccard": round(best_jaccard, 4),
            "best_cluster_id": best_cluster_id,
            "matched": matched,
        }

    return results
