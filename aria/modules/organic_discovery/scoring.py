"""Usefulness scoring for organically discovered capabilities.

Each discovered cluster gets a composite usefulness score (0-100) built from
five measurable components with fixed weights.
"""

from __future__ import annotations

from dataclasses import dataclass

# Weights must sum to 1.0
WEIGHTS: dict[str, float] = {
    "predictability": 0.30,
    "stability": 0.25,
    "entity_coverage": 0.15,
    "activity": 0.15,
    "cohesion": 0.15,
}


def _clamp(value: float) -> float:
    """Clamp a value to the 0.0-1.0 range."""
    return max(0.0, min(1.0, value))


@dataclass
class UsefulnessComponents:
    """Raw component scores for a single capability, each 0.0-1.0.

    - predictability: ML model accuracy for the cluster's entities.
    - stability: how consistently the cluster appears across time windows.
    - entity_coverage: fraction of total entities in this cluster.
    - activity: average daily state changes (normalized).
    - cohesion: silhouette score of the cluster.
    """

    predictability: float
    stability: float
    entity_coverage: float
    activity: float
    cohesion: float

    def to_dict(self) -> dict[str, int]:
        """Return each component as a 0-100 int (clamped)."""
        return {
            "predictability": int(round(_clamp(self.predictability) * 100)),
            "stability": int(round(_clamp(self.stability) * 100)),
            "entity_coverage": int(round(_clamp(self.entity_coverage) * 100)),
            "activity": int(round(_clamp(self.activity) * 100)),
            "cohesion": int(round(_clamp(self.cohesion) * 100)),
        }


def compute_usefulness(components: UsefulnessComponents) -> int:
    """Weighted sum of components, clamped to 0-100, returned as int.

    Weights:
        predictability  30%
        stability       25%
        entity_coverage 15%
        activity        15%
        cohesion        15%
    """
    clamped = {
        "predictability": _clamp(components.predictability),
        "stability": _clamp(components.stability),
        "entity_coverage": _clamp(components.entity_coverage),
        "activity": _clamp(components.activity),
        "cohesion": _clamp(components.cohesion),
    }

    score = sum(clamped[k] * WEIGHTS[k] for k in WEIGHTS)
    return int(round(score * 100))
