#!/usr/bin/env python3
"""HA Intelligence Hub - Main entry point.

Starts the Intelligence Hub with FastAPI server, cache management,
and module orchestration.

Usage:
    ha-hub.py [--port PORT] [--host HOST] [--log-level LEVEL]

Options:
    --port PORT         FastAPI server port (default: 8000)
    --host HOST         FastAPI server host (default: 127.0.0.1)
    --log-level LEVEL   Logging level (default: INFO)
    --cache-dir DIR     Cache directory path (default: ~/ha-logs/intelligence/cache)
"""

import sys
import os
import asyncio
import logging
import signal
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import uvicorn
from hub.core import IntelligenceHub
from hub.api import create_api
from modules.discovery import DiscoveryModule


# Global hub instance for signal handling
hub_instance = None


def setup_logging(log_level: str = "INFO"):
    """Configure logging for hub and modules."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


async def start_hub(cache_path: str) -> IntelligenceHub:
    """Initialize and start the intelligence hub.

    Args:
        cache_path: Path to cache database

    Returns:
        Initialized IntelligenceHub instance
    """
    hub = IntelligenceHub(cache_path)
    await hub.initialize()
    return hub


async def shutdown_hub(hub: IntelligenceHub):
    """Gracefully shutdown the hub."""
    logging.info("Shutting down hub...")
    await hub.shutdown()
    logging.info("Hub shutdown complete")


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logging.info(f"Received signal {signum}, initiating shutdown...")
    if hub_instance:
        asyncio.create_task(shutdown_hub(hub_instance))


def parse_args():
    """Parse command-line arguments."""
    import argparse

    parser = argparse.ArgumentParser(
        description="HA Intelligence Hub - Adaptive home automation intelligence"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="FastAPI server port (default: 8000)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="FastAPI server host (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default=os.path.expanduser("~/ha-logs/intelligence/cache"),
        help="Cache directory path"
    )

    return parser.parse_args()


async def main():
    """Main entry point."""
    global hub_instance

    # Parse arguments
    args = parse_args()

    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger("main")

    # Setup cache path
    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / "hub.db"

    logger.info("=" * 70)
    logger.info("HA Intelligence Hub v0.1.0")
    logger.info("=" * 70)
    logger.info(f"Cache: {cache_path}")
    logger.info(f"Server: http://{args.host}:{args.port}")
    logger.info(f"WebSocket: ws://{args.host}:{args.port}/ws")
    logger.info(f"Log level: {args.log_level}")
    logger.info("=" * 70)

    # Initialize hub
    try:
        hub_instance = await start_hub(str(cache_path))
        logger.info("Hub initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize hub: {e}")
        return 1

    # Get HA credentials from environment
    ha_url = os.environ.get("HA_URL")
    ha_token = os.environ.get("HA_TOKEN")

    if not ha_url or not ha_token:
        logger.error("HA_URL and HA_TOKEN environment variables required")
        logger.error("Source ~/.env before running or export them manually")
        await shutdown_hub(hub_instance)
        return 1

    # Register and initialize discovery module
    try:
        logger.info("Initializing discovery module...")
        discovery = DiscoveryModule(hub_instance, ha_url, ha_token)
        hub_instance.register_module(discovery)
        await discovery.initialize()

        # Schedule periodic discovery (every 24 hours)
        await discovery.schedule_periodic_discovery(interval_hours=24)

        logger.info("Discovery module ready")
    except Exception as e:
        logger.error(f"Failed to initialize discovery module: {e}")
        await shutdown_hub(hub_instance)
        return 1

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create FastAPI app
    app = create_api(hub_instance)

    # Configure uvicorn
    config = uvicorn.Config(
        app,
        host=args.host,
        port=args.port,
        log_level=args.log_level.lower(),
        access_log=True
    )
    server = uvicorn.Server(config)

    # Start server
    try:
        logger.info("Starting FastAPI server...")
        await server.serve()
    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        # Shutdown hub
        await shutdown_hub(hub_instance)

    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nShutdown by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
