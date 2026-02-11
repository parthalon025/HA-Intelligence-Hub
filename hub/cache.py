"""SQLite cache manager with JSON columns and versioning."""

import json
import aiosqlite
import os
from datetime import datetime
from typing import Any, Optional, Dict, List
from pathlib import Path


class CacheManager:
    """Manages SQLite cache for hub data storage."""

    def __init__(self, db_path: str):
        """Initialize cache manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None

    async def initialize(self):
        """Initialize database schema."""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Connect to database
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row

        # Create tables
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                category TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                last_updated TEXT NOT NULL,
                metadata TEXT
            )
        """)

        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                category TEXT,
                data TEXT,
                metadata TEXT
            )
        """)

        await self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_timestamp
            ON events(timestamp DESC)
        """)

        await self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_type
            ON events(event_type)
        """)

        await self._conn.commit()

    async def close(self):
        """Close database connection."""
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def get(self, category: str) -> Optional[Dict[str, Any]]:
        """Get data from cache by category.

        Args:
            category: Cache category (e.g., "entities", "areas")

        Returns:
            Cache entry with data, version, last_updated, metadata or None if not found
        """
        if not self._conn:
            raise RuntimeError("Cache not initialized. Call initialize() first.")

        cursor = await self._conn.execute(
            "SELECT * FROM cache WHERE category = ?",
            (category,)
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return {
            "category": row["category"],
            "data": json.loads(row["data"]),
            "version": row["version"],
            "last_updated": row["last_updated"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else None
        }

    async def set(
        self,
        category: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Set data in cache, incrementing version.

        Args:
            category: Cache category
            data: Data to store (will be JSON-serialized)
            metadata: Optional metadata

        Returns:
            New version number
        """
        if not self._conn:
            raise RuntimeError("Cache not initialized. Call initialize() first.")

        # Get current version
        current = await self.get(category)
        new_version = (current["version"] + 1) if current else 1

        # Store data
        await self._conn.execute(
            """
            INSERT INTO cache (category, data, version, last_updated, metadata)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(category) DO UPDATE SET
                data = excluded.data,
                version = excluded.version,
                last_updated = excluded.last_updated,
                metadata = excluded.metadata
            """,
            (
                category,
                json.dumps(data),
                new_version,
                datetime.now().isoformat(),
                json.dumps(metadata) if metadata else None
            )
        )

        await self._conn.commit()

        # Log event
        await self.log_event(
            event_type="cache_update",
            category=category,
            metadata={"version": new_version}
        )

        return new_version

    async def delete(self, category: str) -> bool:
        """Delete category from cache.

        Args:
            category: Cache category to delete

        Returns:
            True if deleted, False if not found
        """
        if not self._conn:
            raise RuntimeError("Cache not initialized. Call initialize() first.")

        cursor = await self._conn.execute(
            "DELETE FROM cache WHERE category = ?",
            (category,)
        )
        await self._conn.commit()

        deleted = cursor.rowcount > 0
        if deleted:
            await self.log_event(
                event_type="cache_delete",
                category=category
            )

        return deleted

    async def list_categories(self) -> List[str]:
        """List all cache categories.

        Returns:
            List of category names
        """
        if not self._conn:
            raise RuntimeError("Cache not initialized. Call initialize() first.")

        cursor = await self._conn.execute(
            "SELECT category FROM cache ORDER BY category"
        )
        rows = await cursor.fetchall()
        return [row["category"] for row in rows]

    async def log_event(
        self,
        event_type: str,
        category: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log an event to the events table.

        Args:
            event_type: Type of event (e.g., "cache_update", "module_registered")
            category: Related cache category (optional)
            data: Event data (optional)
            metadata: Event metadata (optional)
        """
        if not self._conn:
            raise RuntimeError("Cache not initialized. Call initialize() first.")

        await self._conn.execute(
            """
            INSERT INTO events (timestamp, event_type, category, data, metadata)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(),
                event_type,
                category,
                json.dumps(data) if data else None,
                json.dumps(metadata) if metadata else None
            )
        )
        await self._conn.commit()

    async def get_events(
        self,
        event_type: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recent events from the events table.

        Args:
            event_type: Filter by event type (optional)
            category: Filter by category (optional)
            limit: Maximum number of events to return

        Returns:
            List of events
        """
        if not self._conn:
            raise RuntimeError("Cache not initialized. Call initialize() first.")

        query = "SELECT * FROM events WHERE 1=1"
        params = []

        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor = await self._conn.execute(query, params)
        rows = await cursor.fetchall()

        return [
            {
                "id": row["id"],
                "timestamp": row["timestamp"],
                "event_type": row["event_type"],
                "category": row["category"],
                "data": json.loads(row["data"]) if row["data"] else None,
                "metadata": json.loads(row["metadata"]) if row["metadata"] else None
            }
            for row in rows
        ]
