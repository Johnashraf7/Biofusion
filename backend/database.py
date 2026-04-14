"""
BioFusion AI — SQLite Database Manager
Lightweight async SQLite for search history tracking.
"""

import aiosqlite
import logging
from datetime import datetime
from typing import Dict, List, Optional
from config import DB_PATH

logger = logging.getLogger("biofusion.database")

# ─── Schema ────────────────────────────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    query_type TEXT NOT NULL DEFAULT 'auto',
    timestamp TEXT NOT NULL,
    result_count INTEGER DEFAULT 0,
    cached INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_search_query ON search_history(query);
CREATE INDEX IF NOT EXISTS idx_search_timestamp ON search_history(timestamp);
"""


class Database:
    """Async SQLite database wrapper for BioFusion AI."""

    def __init__(self, db_path: str = str(DB_PATH)):
        self.db_path = db_path
        self._db: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        """Initialize database connection and create tables."""
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(SCHEMA_SQL)
        await self._db.commit()
        logger.info("Database connected: %s", self.db_path)

    async def disconnect(self) -> None:
        """Close the database connection."""
        if self._db:
            await self._db.close()
            self._db = None
            logger.info("Database disconnected")

    async def log_search(
        self,
        query: str,
        query_type: str = "auto",
        result_count: int = 0,
        cached: bool = False,
    ) -> int:
        """Log a search query to history. Returns the row ID."""
        if not self._db:
            raise RuntimeError("Database not connected")

        cursor = await self._db.execute(
            """
            INSERT INTO search_history (query, query_type, timestamp, result_count, cached)
            VALUES (?, ?, ?, ?, ?)
            """,
            (query, query_type, datetime.utcnow().isoformat(), result_count, int(cached)),
        )
        await self._db.commit()
        return cursor.lastrowid

    async def get_recent_searches(self, limit: int = 20) -> List[Dict]:
        """Retrieve recent search history entries."""
        if not self._db:
            raise RuntimeError("Database not connected")

        cursor = await self._db.execute(
            """
            SELECT id, query, query_type, timestamp, result_count, cached
            FROM search_history
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_search_stats(self) -> Dict:
        """Get basic search statistics."""
        if not self._db:
            raise RuntimeError("Database not connected")

        cursor = await self._db.execute(
            """
            SELECT
                COUNT(*) as total_searches,
                COUNT(DISTINCT query) as unique_queries,
                SUM(cached) as cache_hits
            FROM search_history
            """
        )
        row = await cursor.fetchone()
        return dict(row) if row else {"total_searches": 0, "unique_queries": 0, "cache_hits": 0}


# ─── Singleton ─────────────────────────────────────────────────────────────────

db = Database()
