"""
BioFusion AI — File-Based Cache Manager
TTL-based JSON file caching with automatic expiry and invalidation.
"""

import json
import hashlib
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

from config import CACHE_DIR, CACHE_TTL_SECONDS, CACHE_CATEGORIES

logger = logging.getLogger("biofusion.cache")


class FileCache:
    """
    File-based caching system.

    Structure:
        cache/
        ├── gene/
        │   ├── a1b2c3d4.json
        │   └── e5f6g7h8.json
        ├── variant/
        ├── drug/
        ├── disease/
        ├── pathway/
        ├── network/
        └── search/

    Each JSON file contains:
        {
            "timestamp": 1234567890.0,
            "ttl": 604800,
            "key": "original_key",
            "data": { ... actual cached data ... }
        }
    """

    def __init__(
        self,
        cache_dir: Path = CACHE_DIR,
        ttl: int = CACHE_TTL_SECONDS,
    ):
        self.cache_dir = cache_dir
        self.ttl = ttl
        self._init_directories()

    def _init_directories(self) -> None:
        """Create cache directory structure."""
        for category in CACHE_CATEGORIES:
            category_dir = self.cache_dir / category
            category_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Cache initialized at: %s", self.cache_dir)

    @staticmethod
    def _make_hash(key: str) -> str:
        """Create a filesystem-safe hash from a cache key."""
        return hashlib.sha256(key.lower().strip().encode()).hexdigest()[:16]

    def _get_filepath(self, category: str, key: str) -> Path:
        """Get the full path for a cache entry."""
        hashed = self._make_hash(key)
        return self.cache_dir / category / "{}.json".format(hashed)

    def _is_expired(self, entry: Dict) -> bool:
        """Check if a cache entry has exceeded its TTL."""
        created = entry.get("timestamp", 0)
        entry_ttl = entry.get("ttl", self.ttl)
        return (time.time() - created) > entry_ttl

    def get(self, category: str, key: str) -> Optional[Dict]:
        """
        Retrieve a cached entry.

        Returns the cached data dict if valid, None if missing or expired.
        """
        filepath = self._get_filepath(category, key)

        if not filepath.exists():
            logger.debug("Cache MISS: %s/%s", category, key)
            return None

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                entry = json.load(f)

            if self._is_expired(entry):
                logger.debug("Cache EXPIRED: %s/%s", category, key)
                filepath.unlink()
                return None

            logger.debug("Cache HIT: %s/%s", category, key)
            return entry.get("data")

        except (json.JSONDecodeError, IOError) as e:
            logger.warning("Cache read error for %s/%s: %s", category, key, e)
            try:
                filepath.unlink()
            except OSError:
                pass
            return None

    def set(self, category: str, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """
        Store data in the cache.

        Args:
            category: Cache category (gene, variant, drug, etc.)
            key: Cache key (e.g., gene name, variant ID)
            data: Data to cache (must be JSON-serializable)
            ttl: Optional custom TTL in seconds (overrides default)
        """
        filepath = self._get_filepath(category, key)
        entry = {
            "timestamp": time.time(),
            "ttl": ttl if ttl is not None else self.ttl,
            "key": key,
            "data": data,
        }

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(entry, f, indent=2, default=str)
            logger.debug("Cache SET: %s/%s", category, key)
        except IOError as e:
            logger.error("Cache write error for %s/%s: %s", category, key, e)

    def invalidate(self, category: str, key: str) -> bool:
        """Delete a specific cache entry. Returns True if deleted."""
        filepath = self._get_filepath(category, key)
        if filepath.exists():
            filepath.unlink()
            logger.info("Cache INVALIDATED: %s/%s", category, key)
            return True
        return False

    def clear_category(self, category: str) -> int:
        """Clear all entries in a category. Returns count deleted."""
        category_dir = self.cache_dir / category
        count = 0
        if category_dir.exists():
            for f in category_dir.glob("*.json"):
                f.unlink()
                count += 1
        logger.info("Cache category '%s' cleared: %d entries", category, count)
        return count

    def clear_expired(self) -> int:
        """Sweep all categories and delete expired entries. Returns count deleted."""
        count = 0
        for category in CACHE_CATEGORIES:
            category_dir = self.cache_dir / category
            if not category_dir.exists():
                continue

            for filepath in category_dir.glob("*.json"):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        entry = json.load(f)
                    if self._is_expired(entry):
                        filepath.unlink()
                        count += 1
                except (json.JSONDecodeError, IOError):
                    try:
                        filepath.unlink()
                    except OSError:
                        pass
                    count += 1

        logger.info("Cache cleanup: %d expired entries removed", count)
        return count

    def get_stats(self) -> Dict:
        """Get cache statistics per category."""
        stats = {}
        total = 0
        for category in CACHE_CATEGORIES:
            category_dir = self.cache_dir / category
            if category_dir.exists():
                count = len(list(category_dir.glob("*.json")))
                stats[category] = count
                total += count
            else:
                stats[category] = 0
        stats["total"] = total
        return stats


# ─── Singleton ─────────────────────────────────────────────────────────────────

cache = FileCache()
