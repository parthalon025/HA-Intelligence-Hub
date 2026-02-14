"""Tests for organic discovery clustering engine (HDBSCAN)."""

import numpy as np
import pytest

from aria.modules.organic_discovery.clustering import cluster_entities


def _make_two_blobs(n_per_cluster=30, separation=10.0, n_features=5, seed=42):
    """Generate two well-separated clusters for testing."""
    rng = np.random.RandomState(seed)
    center_a = np.zeros(n_features)
    center_b = np.full(n_features, separation)
    blob_a = rng.randn(n_per_cluster, n_features) + center_a
    blob_b = rng.randn(n_per_cluster, n_features) + center_b
    matrix = np.vstack([blob_a, blob_b])
    entity_ids = [f"sensor.entity_{i}" for i in range(2 * n_per_cluster)]
    return matrix, entity_ids


class TestClusterEntities:
    """Tests for the cluster_entities function."""

    def test_finds_two_clusters_in_well_separated_data(self):
        """HDBSCAN should find exactly two clusters in clearly separated blobs."""
        matrix, entity_ids = _make_two_blobs()
        clusters = cluster_entities(matrix, entity_ids, min_cluster_size=5, min_samples=3)
        assert len(clusters) == 2

    def test_returns_correct_structure(self):
        """Each cluster dict must have cluster_id, entity_ids, silhouette keys."""
        matrix, entity_ids = _make_two_blobs()
        clusters = cluster_entities(matrix, entity_ids, min_cluster_size=5, min_samples=3)
        assert len(clusters) > 0
        for cluster in clusters:
            assert "cluster_id" in cluster
            assert "entity_ids" in cluster
            assert "silhouette" in cluster
            assert isinstance(cluster["cluster_id"], int)
            assert isinstance(cluster["entity_ids"], list)
            assert isinstance(cluster["silhouette"], float)

    def test_assigns_most_entities(self):
        """At least 80% of entities should be assigned (not noise) in clean data."""
        matrix, entity_ids = _make_two_blobs()
        clusters = cluster_entities(matrix, entity_ids, min_cluster_size=5, min_samples=3)
        assigned = sum(len(c["entity_ids"]) for c in clusters)
        assert assigned >= 0.8 * len(entity_ids)

    def test_separates_distinct_groups(self):
        """Entities from blob A and blob B should land in different clusters."""
        n = 30
        matrix, entity_ids = _make_two_blobs(n_per_cluster=n)
        clusters = cluster_entities(matrix, entity_ids, min_cluster_size=5, min_samples=3)

        # Build mapping: entity_id -> cluster_id
        entity_to_cluster = {}
        for c in clusters:
            for eid in c["entity_ids"]:
                entity_to_cluster[eid] = c["cluster_id"]

        # Most of first-half entities (blob A) should share one cluster,
        # most of second-half (blob B) should share a different cluster.
        cluster_ids_a = {entity_to_cluster.get(f"sensor.entity_{i}") for i in range(n)} - {None}
        cluster_ids_b = {entity_to_cluster.get(f"sensor.entity_{i}") for i in range(n, 2 * n)} - {None}

        # Each blob should predominantly map to a single cluster
        assert len(cluster_ids_a) == 1
        assert len(cluster_ids_b) == 1
        # And they should be different clusters
        assert cluster_ids_a != cluster_ids_b

    def test_handles_small_input_gracefully(self):
        """Fewer entities than min_cluster_size should return empty list, not crash."""
        rng = np.random.RandomState(99)
        matrix = rng.randn(3, 5)
        entity_ids = ["sensor.a", "sensor.b", "sensor.c"]
        clusters = cluster_entities(matrix, entity_ids, min_cluster_size=5, min_samples=3)
        assert isinstance(clusters, list)
        # With only 3 points and min_cluster_size=5, no clusters possible
        assert len(clusters) == 0

    def test_silhouette_scores_in_valid_range(self):
        """Silhouette scores must be in [-1, 1]."""
        matrix, entity_ids = _make_two_blobs()
        clusters = cluster_entities(matrix, entity_ids, min_cluster_size=5, min_samples=3)
        for cluster in clusters:
            assert -1.0 <= cluster["silhouette"] <= 1.0

    def test_empty_input(self):
        """Empty matrix should return empty list."""
        matrix = np.empty((0, 5))
        entity_ids = []
        clusters = cluster_entities(matrix, entity_ids)
        assert clusters == []

    def test_single_cluster_no_silhouette_crash(self):
        """When all points form one cluster, silhouette can't be computed meaningfully.
        Should still return a result without crashing."""
        rng = np.random.RandomState(7)
        # Tight single blob — HDBSCAN may find 1 cluster or 0
        matrix = rng.randn(20, 3) * 0.1
        entity_ids = [f"light.room_{i}" for i in range(20)]
        clusters = cluster_entities(matrix, entity_ids, min_cluster_size=5, min_samples=3)
        assert isinstance(clusters, list)
        # If a cluster was found, structure should still be valid
        for cluster in clusters:
            assert "cluster_id" in cluster
            assert "entity_ids" in cluster
            assert "silhouette" in cluster

    def test_entity_ids_length_mismatch_raises(self):
        """Matrix rows must match entity_ids length."""
        matrix = np.random.randn(10, 5)
        entity_ids = ["sensor.a", "sensor.b"]
        with pytest.raises(ValueError):
            cluster_entities(matrix, entity_ids)

    def test_custom_min_cluster_size(self):
        """Larger min_cluster_size should still work and may produce fewer clusters."""
        matrix, entity_ids = _make_two_blobs(n_per_cluster=50)
        clusters = cluster_entities(matrix, entity_ids, min_cluster_size=15, min_samples=5)
        # Should still find the two blobs with larger min size
        assert len(clusters) >= 1
        for c in clusters:
            assert len(c["entity_ids"]) >= 15
