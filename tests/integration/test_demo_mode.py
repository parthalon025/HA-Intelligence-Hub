"""Tests for aria demo mode CLI integration."""
import pytest
from pathlib import Path
from tests.demo.generate import generate_checkpoint


class TestDemoGenerate:
    def test_generate_checkpoint(self, tmp_path):
        output = generate_checkpoint(
            scenario="stable_couple",
            days=14,
            seed=42,
            output_dir=tmp_path / "day_14",
        )
        assert (tmp_path / "day_14").exists()
        assert (tmp_path / "day_14" / "daily").exists()
        assert len(list((tmp_path / "day_14" / "daily").glob("*.json"))) == 14
        assert output["snapshots_saved"] == 14

    def test_generate_multiple_checkpoints(self, tmp_path):
        for name, days in [("day_07", 7), ("day_14", 14)]:
            output = generate_checkpoint(
                scenario="stable_couple",
                days=days,
                seed=42,
                output_dir=tmp_path / name,
            )
            assert output["snapshots_saved"] == days
