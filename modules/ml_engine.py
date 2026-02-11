"""ML Engine Module - Adaptive machine learning predictions.

Trains sklearn models based on discovered capabilities and generates predictions
for home automation metrics (power, lights, occupancy, etc.).

Architecture:
- Reads capabilities from hub cache to determine what to predict
- Trains separate models per capability (GradientBoosting, RandomForest, blend)
- Stores trained models and predictions back to hub cache
- Runs training on schedule (weekly) and prediction daily
"""

import os
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor, IsolationForest
from sklearn.preprocessing import StandardScaler

from hub.core import Module, IntelligenceHub


logger = logging.getLogger(__name__)


class MLEngine(Module):
    """Machine learning prediction engine with adaptive capability mapping."""

    def __init__(
        self,
        hub: IntelligenceHub,
        models_dir: str,
        training_data_dir: str
    ):
        """Initialize ML engine.

        Args:
            hub: IntelligenceHub instance
            models_dir: Directory to store trained models
            training_data_dir: Directory with historical snapshots for training
        """
        super().__init__("ml_engine", hub)
        self.models_dir = Path(models_dir)
        self.training_data_dir = Path(training_data_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Capability to prediction mapping
        # Maps discovered capabilities to what we should predict
        self.capability_predictions = {
            "power_monitoring": ["power_watts"],
            "lighting": ["lights_on", "total_brightness"],
            "occupancy": ["people_home", "devices_home"],
            "motion": ["motion_active_count"],
            "climate": ["temperature", "humidity"],
        }

        # Loaded models cache
        self.models: Dict[str, Dict[str, Any]] = {}

    async def initialize(self):
        """Initialize module - load existing models."""
        self.logger.info("ML Engine initializing...")

        # Load capabilities from hub cache
        capabilities_entry = await self.hub.get_cache("capabilities")
        if not capabilities_entry:
            self.logger.warning("No capabilities found in cache. Run discovery first.")
            return

        capabilities = capabilities_entry.get("data", {})
        self.logger.info(f"Found {len(capabilities)} capabilities in cache")

        # Load existing models
        await self._load_models()

        self.logger.info("ML Engine initialized")

    async def _load_models(self):
        """Load trained models from disk."""
        for model_file in self.models_dir.glob("*.pkl"):
            try:
                with open(model_file, "rb") as f:
                    model_data = pickle.load(f)

                model_name = model_file.stem
                self.models[model_name] = model_data
                self.logger.info(f"Loaded model: {model_name}")

            except Exception as e:
                self.logger.error(f"Failed to load model {model_file}: {e}")

    async def train_models(self, days_history: int = 60):
        """Train models using historical data.

        Args:
            days_history: Number of days of historical data to use for training
        """
        self.logger.info(f"Training models with {days_history} days of history...")

        # Get capabilities to determine what to train
        capabilities_entry = await self.hub.get_cache("capabilities")
        if not capabilities_entry:
            self.logger.error("No capabilities in cache. Cannot train without discovery data.")
            return

        capabilities = capabilities_entry.get("data", {})

        # Load training data
        training_data = await self._load_training_data(days_history)
        if not training_data:
            self.logger.error("No training data available")
            return

        self.logger.info(f"Loaded {len(training_data)} snapshots for training")

        # Train models for each available capability
        for capability_name, capability_data in capabilities.items():
            if not capability_data.get("available"):
                continue

            # Check if we have predictions defined for this capability
            prediction_targets = self.capability_predictions.get(capability_name)
            if not prediction_targets:
                self.logger.debug(f"No prediction targets defined for {capability_name}")
                continue

            self.logger.info(f"Training models for capability: {capability_name}")

            for target in prediction_targets:
                try:
                    await self._train_model_for_target(
                        target,
                        training_data,
                        capability_name
                    )
                except Exception as e:
                    self.logger.error(f"Failed to train model for {target}: {e}")

        self.logger.info("Model training complete")

        # Store training metadata in cache
        await self.hub.set_cache(
            "ml_training_metadata",
            {
                "last_trained": datetime.now().isoformat(),
                "days_history": days_history,
                "num_snapshots": len(training_data),
                "capabilities_trained": list(capabilities.keys())
            }
        )

    async def _load_training_data(self, days: int) -> List[Dict[str, Any]]:
        """Load historical snapshots for training.

        Args:
            days: Number of days to load

        Returns:
            List of snapshot dictionaries
        """
        snapshots = []
        today = datetime.now()

        for i in range(days):
            date_str = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            snapshot_file = self.training_data_dir / f"{date_str}.json"

            if snapshot_file.exists():
                try:
                    with open(snapshot_file) as f:
                        snapshot = json.load(f)
                        snapshots.append(snapshot)
                except (json.JSONDecodeError, IOError) as e:
                    self.logger.warning(f"Failed to load snapshot {snapshot_file}: {e}")

        return snapshots

    async def _train_model_for_target(
        self,
        target: str,
        training_data: List[Dict[str, Any]],
        capability_name: str
    ):
        """Train a model for a specific prediction target.

        Args:
            target: Target metric to predict (e.g., "power_watts")
            training_data: List of historical snapshots
            capability_name: Capability this target belongs to
        """
        self.logger.info(f"Training model for target: {target}")

        # Extract features and target values
        X, y = self._build_training_dataset(training_data, target)

        if len(X) < 10:
            self.logger.warning(f"Insufficient training data for {target}: {len(X)} samples")
            return

        # Train GradientBoosting model
        gb_model = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=3,
            random_state=42
        )
        gb_model.fit(X, y)

        # Train RandomForest model
        rf_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=5,
            random_state=42
        )
        rf_model.fit(X, y)

        # Create scaler for feature normalization
        scaler = StandardScaler()
        scaler.fit(X)

        # Store model data
        model_data = {
            "target": target,
            "capability": capability_name,
            "gb_model": gb_model,
            "rf_model": rf_model,
            "scaler": scaler,
            "trained_at": datetime.now().isoformat(),
            "num_samples": len(X),
            "feature_names": self._get_feature_names(training_data[0] if training_data else {})
        }

        # Save to disk
        model_file = self.models_dir / f"{target}_model.pkl"
        with open(model_file, "wb") as f:
            pickle.dump(model_data, f)

        # Cache in memory
        self.models[target] = model_data

        self.logger.info(
            f"Model trained for {target}: "
            f"{len(X)} samples, {len(model_data['feature_names'])} features"
        )

    def _build_training_dataset(
        self,
        snapshots: List[Dict[str, Any]],
        target: str
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Build training dataset from snapshots.

        Args:
            snapshots: List of historical snapshots
            target: Target metric to extract

        Returns:
            Tuple of (features, targets) as numpy arrays
        """
        X_list = []
        y_list = []

        for snapshot in snapshots:
            # Extract features
            features = self._extract_features(snapshot)
            if features is None:
                continue

            # Extract target value
            target_value = self._extract_target(snapshot, target)
            if target_value is None:
                continue

            X_list.append(list(features.values()))
            y_list.append(target_value)

        if not X_list:
            return np.array([]), np.array([])

        return np.array(X_list), np.array(y_list)

    def _extract_features(self, snapshot: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """Extract feature vector from snapshot.

        Args:
            snapshot: Snapshot dictionary

        Returns:
            Dictionary of feature_name -> value
        """
        # Simplified feature extraction - in real implementation, this would be
        # much more comprehensive and use the feature config from ha-intelligence
        features = {}

        # Time features
        time_features = snapshot.get("time_features", {})
        features["hour_sin"] = time_features.get("hour_sin", 0)
        features["hour_cos"] = time_features.get("hour_cos", 0)
        features["is_weekend"] = 1 if time_features.get("is_weekend") else 0

        # Weather features
        weather = snapshot.get("weather", {})
        features["temp_f"] = weather.get("temp_f", 0) or 0
        features["humidity_pct"] = weather.get("humidity_pct", 0) or 0

        # Home state features
        occupancy = snapshot.get("occupancy", {})
        features["people_home"] = occupancy.get("people_home_count", 0)

        lights = snapshot.get("lights", {})
        features["lights_on"] = lights.get("on", 0)

        return features

    def _extract_target(self, snapshot: Dict[str, Any], target: str) -> Optional[float]:
        """Extract target value from snapshot.

        Args:
            snapshot: Snapshot dictionary
            target: Target metric name

        Returns:
            Target value or None if not available
        """
        # Map target names to snapshot locations
        target_map = {
            "power_watts": ("power", "total_watts"),
            "lights_on": ("lights", "on"),
            "total_brightness": ("lights", "total_brightness"),
            "people_home": ("occupancy", "people_home_count"),
            "devices_home": ("occupancy", "device_count_home"),
            "motion_active_count": ("motion", "active_count"),
        }

        if target not in target_map:
            return None

        section, key = target_map[target]
        value = snapshot.get(section, {}).get(key)

        return float(value) if value is not None else None

    def _get_feature_names(self, snapshot: Dict[str, Any]) -> List[str]:
        """Get list of feature names used in training.

        Args:
            snapshot: Sample snapshot

        Returns:
            List of feature names
        """
        features = self._extract_features(snapshot)
        return list(features.keys()) if features else []

    async def generate_predictions(self) -> Dict[str, Any]:
        """Generate predictions for tomorrow using trained models.

        Returns:
            Dictionary of predictions by target
        """
        self.logger.info("Generating predictions...")

        if not self.models:
            self.logger.warning("No models loaded. Train models first.")
            return {}

        # Get current state from cache to use as features
        # In real implementation, this would fetch the latest snapshot
        # For now, return placeholder
        predictions = {
            "timestamp": datetime.now().isoformat(),
            "predictions": {},
            "model_count": len(self.models)
        }

        self.logger.info(f"Generated predictions for {len(self.models)} targets")

        # Store predictions in cache
        await self.hub.set_cache("ml_predictions", predictions)

        return predictions

    async def on_event(self, event_type: str, data: Dict[str, Any]):
        """Handle hub events.

        Args:
            event_type: Type of event
            data: Event data
        """
        # ML module could respond to cache updates
        # e.g., when new discovery data available, retrain models
        if event_type == "cache_updated" and data.get("category") == "capabilities":
            self.logger.info("Capabilities updated - models may need retraining")

    async def schedule_periodic_training(self, interval_days: int = 7):
        """Schedule periodic model retraining.

        Args:
            interval_days: Days between training runs
        """
        async def training_task():
            try:
                await self.train_models(days_history=60)
            except Exception as e:
                self.logger.error(f"Scheduled training failed: {e}")

        await self.hub.schedule_task(
            task_id="ml_training_periodic",
            coro=training_task,
            interval=timedelta(days=interval_days),
            run_immediately=False
        )

        self.logger.info(f"Scheduled periodic training every {interval_days} days")
