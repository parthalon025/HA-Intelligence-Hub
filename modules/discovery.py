"""Discovery Module - HA entity and capability detection.

Wraps the standalone discover.py script and integrates it with the hub.
Runs discovery on a schedule and stores results in hub cache.
"""

import os
import sys
import json
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import timedelta

from hub.core import Module, IntelligenceHub


logger = logging.getLogger(__name__)


class DiscoveryModule(Module):
    """Discovers HA entities, devices, areas, and capabilities."""

    def __init__(self, hub: IntelligenceHub, ha_url: str, ha_token: str):
        """Initialize discovery module.

        Args:
            hub: IntelligenceHub instance
            ha_url: Home Assistant URL (e.g., "http://192.168.1.35:8123")
            ha_token: Home Assistant long-lived access token
        """
        super().__init__("discovery", hub)
        self.ha_url = ha_url
        self.ha_token = ha_token
        self.discover_script = Path(__file__).parent.parent / "bin" / "discover.py"

        if not self.discover_script.exists():
            raise FileNotFoundError(f"Discovery script not found: {self.discover_script}")

    async def initialize(self):
        """Initialize module - run initial discovery."""
        self.logger.info("Discovery module initializing...")

        # Run initial discovery
        try:
            await self.run_discovery()
            self.logger.info("Initial discovery complete")
        except Exception as e:
            self.logger.error(f"Initial discovery failed: {e}")

    async def run_discovery(self) -> Dict[str, Any]:
        """Run discovery script and store results in hub cache.

        Returns:
            Discovery results dictionary
        """
        self.logger.info("Running discovery...")

        try:
            # Run discover.py subprocess
            result = subprocess.run(
                [sys.executable, str(self.discover_script)],
                capture_output=True,
                text=True,
                timeout=120,
                env={
                    **os.environ,
                    "HA_URL": self.ha_url,
                    "HA_TOKEN": self.ha_token
                }
            )

            if result.returncode != 0:
                error_msg = result.stderr or "Unknown error"
                raise RuntimeError(f"Discovery failed: {error_msg}")

            # Parse JSON output
            capabilities = json.loads(result.stdout)

            # Store in hub cache
            await self._store_discovery_results(capabilities)

            self.logger.info(
                f"Discovery complete: {capabilities.get('entity_count', 0)} entities, "
                f"{len(capabilities.get('capabilities', {}))} capabilities"
            )

            return capabilities

        except subprocess.TimeoutExpired:
            self.logger.error("Discovery timed out after 120 seconds")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse discovery output: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Discovery error: {e}")
            raise

    async def _store_discovery_results(self, capabilities: Dict[str, Any]):
        """Store discovery results in hub cache.

        Stores separate cache entries for:
        - entities: Entity registry data
        - devices: Device registry data
        - areas: Area registry data
        - capabilities: Detected capabilities
        - discovery_metadata: Discovery run metadata
        """
        # Store entities
        entities = capabilities.get("entities", {})
        if entities:
            await self.hub.set_cache("entities", entities, {
                "count": len(entities),
                "source": "discovery"
            })

        # Store devices
        devices = capabilities.get("devices", {})
        if devices:
            await self.hub.set_cache("devices", devices, {
                "count": len(devices),
                "source": "discovery"
            })

        # Store areas
        areas = capabilities.get("areas", {})
        if areas:
            await self.hub.set_cache("areas", areas, {
                "count": len(areas),
                "source": "discovery"
            })

        # Store capabilities
        caps = capabilities.get("capabilities", {})
        if caps:
            await self.hub.set_cache("capabilities", caps, {
                "count": len(caps),
                "source": "discovery"
            })

        # Store metadata
        metadata = {
            "entity_count": capabilities.get("entity_count", 0),
            "device_count": capabilities.get("device_count", 0),
            "area_count": capabilities.get("area_count", 0),
            "capability_count": len(caps),
            "timestamp": capabilities.get("timestamp"),
            "ha_version": capabilities.get("ha_version")
        }
        await self.hub.set_cache("discovery_metadata", metadata)

    async def on_event(self, event_type: str, data: Dict[str, Any]):
        """Handle hub events.

        Args:
            event_type: Type of event
            data: Event data
        """
        # Discovery module doesn't need to respond to events currently
        # Could add automatic re-discovery on certain events in the future
        pass

    async def schedule_periodic_discovery(self, interval_hours: int = 24):
        """Schedule periodic discovery runs.

        Args:
            interval_hours: Hours between discovery runs
        """
        async def discovery_task():
            try:
                await self.run_discovery()
            except Exception as e:
                self.logger.error(f"Scheduled discovery failed: {e}")

        await self.hub.schedule_task(
            task_id="discovery_periodic",
            coro=discovery_task,
            interval=timedelta(hours=interval_hours),
            run_immediately=False  # Initial discovery already done
        )

        self.logger.info(f"Scheduled periodic discovery every {interval_hours} hours")
