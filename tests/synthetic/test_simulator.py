"""Tests for HouseholdSimulator and scenarios."""
import pytest
from tests.synthetic.simulator import HouseholdSimulator


class TestHouseholdSimulator:
    def test_stable_couple_scenario(self):
        sim = HouseholdSimulator(scenario="stable_couple", days=7, seed=42)
        snapshots = sim.generate()
        assert len(snapshots) == 7

    def test_new_roommate_scenario(self):
        sim = HouseholdSimulator(scenario="new_roommate", days=21, seed=42)
        snapshots = sim.generate()
        assert len(snapshots) == 21

    def test_vacation_scenario(self):
        sim = HouseholdSimulator(scenario="vacation", days=14, seed=42)
        snapshots = sim.generate()
        assert len(snapshots) == 14

    def test_work_from_home_scenario(self):
        sim = HouseholdSimulator(scenario="work_from_home", days=14, seed=42)
        snapshots = sim.generate()
        assert len(snapshots) == 14

    def test_sensor_degradation_scenario(self):
        sim = HouseholdSimulator(scenario="sensor_degradation", days=14, seed=42)
        snapshots = sim.generate()
        assert len(snapshots) == 14

    def test_unknown_scenario_raises(self):
        with pytest.raises(ValueError, match="Unknown scenario"):
            HouseholdSimulator(scenario="nonexistent", days=7, seed=42)

    def test_deterministic(self):
        a = HouseholdSimulator(scenario="stable_couple", days=7, seed=42).generate()
        b = HouseholdSimulator(scenario="stable_couple", days=7, seed=42).generate()
        for sa, sb in zip(a, b):
            assert sa["power"]["total_watts"] == sb["power"]["total_watts"]

    def test_snapshots_have_variation(self):
        sim = HouseholdSimulator(scenario="stable_couple", days=14, seed=42)
        snapshots = sim.generate()
        powers = [s["power"]["total_watts"] for s in snapshots]
        assert len(set(powers)) > 1

    def test_vacation_has_low_occupancy_midweek(self):
        sim = HouseholdSimulator(scenario="vacation", days=14, seed=42)
        snapshots = sim.generate()
        # Days 10-17 (0-indexed: 9-16) both residents should be away
        # Check a few vacation days
        for i in range(10, min(14, len(snapshots))):
            s = snapshots[i]
            people_home = s["occupancy"].get("people_home", [])
            # During vacation, nobody should be home
            assert len(people_home) == 0, f"Day {i}: expected empty house, got {people_home}"
