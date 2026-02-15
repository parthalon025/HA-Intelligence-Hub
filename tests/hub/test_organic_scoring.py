"""Tests for organic discovery usefulness scoring."""


from aria.modules.organic_discovery.scoring import (
    UsefulnessComponents,
    compute_usefulness,
)


class TestUsefulnessComponents:
    """Tests for UsefulnessComponents dataclass."""

    def test_to_dict_all_ones(self):
        c = UsefulnessComponents(
            predictability=1.0,
            stability=1.0,
            entity_coverage=1.0,
            activity=1.0,
            cohesion=1.0,
        )
        result = c.to_dict()
        assert result == {
            "predictability": 100,
            "stability": 100,
            "entity_coverage": 100,
            "activity": 100,
            "cohesion": 100,
        }

    def test_to_dict_all_zeros(self):
        c = UsefulnessComponents(
            predictability=0.0,
            stability=0.0,
            entity_coverage=0.0,
            activity=0.0,
            cohesion=0.0,
        )
        result = c.to_dict()
        assert result == {
            "predictability": 0,
            "stability": 0,
            "entity_coverage": 0,
            "activity": 0,
            "cohesion": 0,
        }

    def test_to_dict_returns_ints(self):
        c = UsefulnessComponents(
            predictability=0.5,
            stability=0.3,
            entity_coverage=0.75,
            activity=0.1,
            cohesion=0.9,
        )
        result = c.to_dict()
        for key, value in result.items():
            assert isinstance(value, int), f"{key} should be int, got {type(value)}"

    def test_to_dict_mixed_values(self):
        c = UsefulnessComponents(
            predictability=0.5,
            stability=0.25,
            entity_coverage=0.75,
            activity=0.0,
            cohesion=1.0,
        )
        result = c.to_dict()
        assert result == {
            "predictability": 50,
            "stability": 25,
            "entity_coverage": 75,
            "activity": 0,
            "cohesion": 100,
        }

    def test_to_dict_clamps_above_one(self):
        c = UsefulnessComponents(
            predictability=1.5,
            stability=2.0,
            entity_coverage=1.0,
            activity=0.5,
            cohesion=0.5,
        )
        result = c.to_dict()
        assert result["predictability"] == 100
        assert result["stability"] == 100

    def test_to_dict_clamps_below_zero(self):
        c = UsefulnessComponents(
            predictability=-0.5,
            stability=0.5,
            entity_coverage=0.5,
            activity=0.5,
            cohesion=0.5,
        )
        result = c.to_dict()
        assert result["predictability"] == 0


class TestComputeUsefulness:
    """Tests for compute_usefulness function."""

    def test_all_perfect_returns_100(self):
        c = UsefulnessComponents(
            predictability=1.0,
            stability=1.0,
            entity_coverage=1.0,
            activity=1.0,
            cohesion=1.0,
        )
        assert compute_usefulness(c) == 100

    def test_all_zero_returns_0(self):
        c = UsefulnessComponents(
            predictability=0.0,
            stability=0.0,
            entity_coverage=0.0,
            activity=0.0,
            cohesion=0.0,
        )
        assert compute_usefulness(c) == 0

    def test_predictability_weight_greater_than_stability(self):
        """Predictability (30%) should contribute more than stability (25%)."""
        pred_only = UsefulnessComponents(
            predictability=1.0,
            stability=0.0,
            entity_coverage=0.0,
            activity=0.0,
            cohesion=0.0,
        )
        stab_only = UsefulnessComponents(
            predictability=0.0,
            stability=1.0,
            entity_coverage=0.0,
            activity=0.0,
            cohesion=0.0,
        )
        assert compute_usefulness(pred_only) > compute_usefulness(stab_only)

    def test_returns_int(self):
        c = UsefulnessComponents(
            predictability=0.5,
            stability=0.3,
            entity_coverage=0.75,
            activity=0.1,
            cohesion=0.9,
        )
        result = compute_usefulness(c)
        assert isinstance(result, int)

    def test_returns_in_0_100_range(self):
        c = UsefulnessComponents(
            predictability=0.42,
            stability=0.88,
            entity_coverage=0.33,
            activity=0.67,
            cohesion=0.15,
        )
        result = compute_usefulness(c)
        assert 0 <= result <= 100

    def test_clamps_values_above_one(self):
        c = UsefulnessComponents(
            predictability=2.0,
            stability=2.0,
            entity_coverage=2.0,
            activity=2.0,
            cohesion=2.0,
        )
        assert compute_usefulness(c) == 100

    def test_clamps_values_below_zero(self):
        c = UsefulnessComponents(
            predictability=-1.0,
            stability=-1.0,
            entity_coverage=-1.0,
            activity=-1.0,
            cohesion=-1.0,
        )
        assert compute_usefulness(c) == 0

    def test_known_weighted_sum(self):
        """Verify exact weighted computation.

        Weights: pred=0.30, stab=0.25, cov=0.15, act=0.15, coh=0.15
        Components: 0.8, 0.6, 0.4, 0.2, 1.0
        Expected: 0.8*30 + 0.6*25 + 0.4*15 + 0.2*15 + 1.0*15
                = 24 + 15 + 6 + 3 + 15 = 63
        """
        c = UsefulnessComponents(
            predictability=0.8,
            stability=0.6,
            entity_coverage=0.4,
            activity=0.2,
            cohesion=1.0,
        )
        assert compute_usefulness(c) == 63

    def test_predictability_only_gives_30(self):
        c = UsefulnessComponents(
            predictability=1.0,
            stability=0.0,
            entity_coverage=0.0,
            activity=0.0,
            cohesion=0.0,
        )
        assert compute_usefulness(c) == 30

    def test_stability_only_gives_25(self):
        c = UsefulnessComponents(
            predictability=0.0,
            stability=1.0,
            entity_coverage=0.0,
            activity=0.0,
            cohesion=0.0,
        )
        assert compute_usefulness(c) == 25

    def test_each_15_percent_weight(self):
        """entity_coverage, activity, and cohesion each contribute 15%."""
        for field in ("entity_coverage", "activity", "cohesion"):
            kwargs = {
                "predictability": 0.0,
                "stability": 0.0,
                "entity_coverage": 0.0,
                "activity": 0.0,
                "cohesion": 0.0,
            }
            kwargs[field] = 1.0
            c = UsefulnessComponents(**kwargs)
            assert compute_usefulness(c) == 15, f"{field} should contribute 15"
