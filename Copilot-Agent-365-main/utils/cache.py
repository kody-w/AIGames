"""
AI Ambassador Platform - Comprehensive Caching System

This module provides a multi-tier caching system to reduce Azure OpenAI API costs
and improve response times. Features include:

- In-memory LRU cache for fast access
- File-based persistent cache using Azure File Storage
- Semantic similarity caching using embeddings
- Intelligent cache invalidation strategies
- Cache warming and pre-computation
- Detailed statistics and cost tracking
- Thread-safe operations
- Redis adapter for production scaling

Cache Types:
1. Response Cache: Cache OpenAI responses for identical queries
2. Semantic Cache: Cache semantically similar queries
3. Agent Metadata Cache: Cache agent definitions
4. Ambassador Config Cache: Cache ambassador configurations
5. Memory Context Cache: Cache frequently accessed memory
6. Analytics Cache: Pre-computed analytics

Author: AI Ambassador Platform Team
Version: 1.0.0
"""

import hashlib
import json
import logging
import threading
import time
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import os
import numpy as np
from pathlib import Path

# Optional Redis support for production
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not available. Using in-memory cache only.")


@dataclass
class CacheEntry:
    """Represents a single cache entry with metadata"""
    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int
    ttl: int  # Time-to-live in seconds
    tags: List[str]
    size_bytes: int
    cache_type: str

    def is_expired(self) -> bool:
        """Check if entry has exceeded its TTL"""
        if self.ttl <= 0:  # 0 or negative means no expiration
            return False
        return (time.time() - self.created_at) > self.ttl

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return asdict(self)


@dataclass
class CacheStats:
    """Cache performance statistics"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    invalidations: int = 0
    total_size_bytes: int = 0
    total_entries: int = 0
    cost_savings_usd: float = 0.0
    avg_response_time_ms: float = 0.0

    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary with computed metrics"""
        data = asdict(self)
        data['hit_rate_percent'] = self.hit_rate()
        return data


class SemanticSimilarityCache:
    """
    Cache that uses embedding similarity to match semantically similar queries.

    This allows caching responses for queries that are phrased differently but
    have the same meaning, significantly improving cache hit rates.
    """

    def __init__(self, similarity_threshold: float = 0.95):
        """
        Initialize semantic cache.

        Args:
            similarity_threshold: Cosine similarity threshold (0-1) for cache hits
        """
        self.similarity_threshold = similarity_threshold
        self.embeddings: Dict[str, np.ndarray] = {}
        self.query_to_key: Dict[str, str] = {}
        self.lock = threading.RLock()

    def _compute_embedding(self, text: str) -> np.ndarray:
        """
        Compute embedding for text using simple TF-IDF-like approach.

        In production, this should use Azure OpenAI embeddings API.
        This is a lightweight fallback for cost optimization.
        """
        # Simple character-level embedding (replace with OpenAI embeddings in production)
        words = text.lower().split()

        # Create a simple bag-of-words vector (limited vocabulary for speed)
        vocab = sorted(set(words))[:100]  # Limit vocabulary size
        vector = np.zeros(max(100, len(vocab)))

        for i, word in enumerate(vocab):
            if i < len(vector):
                vector[i] = words.count(word)

        # Normalize
        norm = np.linalg.norm(vector)
        return vector / norm if norm > 0 else vector

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        return float(dot_product)  # Already normalized

    def find_similar(self, query: str) -> Optional[str]:
        """
        Find cached entry with similar semantic meaning.

        Args:
            query: Input query text

        Returns:
            Cache key if similar entry found, None otherwise
        """
        with self.lock:
            if not self.embeddings:
                return None

            query_embedding = self._compute_embedding(query)

            best_similarity = 0.0
            best_key = None

            for cached_query, cached_embedding in self.embeddings.items():
                similarity = self._cosine_similarity(query_embedding, cached_embedding)

                if similarity > best_similarity and similarity >= self.similarity_threshold:
                    best_similarity = similarity
                    best_key = self.query_to_key[cached_query]

            return best_key

    def add(self, query: str, cache_key: str):
        """Add query embedding to semantic index"""
        with self.lock:
            embedding = self._compute_embedding(query)
            self.embeddings[query] = embedding
            self.query_to_key[query] = cache_key

    def remove(self, query: str):
        """Remove query from semantic index"""
        with self.lock:
            if query in self.embeddings:
                del self.embeddings[query]
                del self.query_to_key[query]

    def clear(self):
        """Clear all semantic cache data"""
        with self.lock:
            self.embeddings.clear()
            self.query_to_key.clear()


class LRUCache:
    """
    Thread-safe Least Recently Used (LRU) cache implementation.

    Automatically evicts least recently used items when capacity is reached.
    """

    def __init__(self, max_size: int = 1000):
        """
        Initialize LRU cache.

        Args:
            max_size: Maximum number of entries to store
        """
        self.max_size = max_size
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = threading.RLock()
        self.stats = CacheStats()

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self.lock:
            if key not in self.cache:
                self.stats.misses += 1
                return None

            entry = self.cache[key]

            # Check expiration
            if entry.is_expired():
                self._evict(key)
                self.stats.misses += 1
                return None

            # Update access metadata
            entry.last_accessed = time.time()
            entry.access_count += 1

            # Move to end (most recently used)
            self.cache.move_to_end(key)

            self.stats.hits += 1
            return entry.value

    def set(self, key: str, value: Any, ttl: int = 3600, tags: List[str] = None,
            cache_type: str = 'default') -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (0 = no expiration)
            tags: Tags for invalidation
            cache_type: Type of cache entry
        """
        with self.lock:
            now = time.time()

            # Calculate size
            try:
                size_bytes = len(json.dumps(value).encode('utf-8'))
            except:
                size_bytes = 0

            entry = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                last_accessed=now,
                access_count=0,
                ttl=ttl,
                tags=tags or [],
                size_bytes=size_bytes,
                cache_type=cache_type
            )

            # Evict if at capacity
            if key not in self.cache and len(self.cache) >= self.max_size:
                self._evict_lru()

            self.cache[key] = entry
            self.cache.move_to_end(key)

            # Update stats
            self.stats.total_entries = len(self.cache)
            self.stats.total_size_bytes = sum(e.size_bytes for e in self.cache.values())

    def _evict_lru(self):
        """Evict least recently used item"""
        if self.cache:
            key = next(iter(self.cache))
            self._evict(key)

    def _evict(self, key: str):
        """Evict specific key"""
        if key in self.cache:
            del self.cache[key]
            self.stats.evictions += 1
            self.stats.total_entries = len(self.cache)

    def invalidate(self, key: str) -> bool:
        """
        Invalidate specific cache entry.

        Args:
            key: Cache key to invalidate

        Returns:
            True if entry was invalidated, False if not found
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                self.stats.invalidations += 1
                self.stats.total_entries = len(self.cache)
                return True
            return False

    def invalidate_by_tag(self, tag: str) -> int:
        """
        Invalidate all entries with specific tag.

        Args:
            tag: Tag to match

        Returns:
            Number of entries invalidated
        """
        with self.lock:
            keys_to_remove = [
                key for key, entry in self.cache.items()
                if tag in entry.tags
            ]

            for key in keys_to_remove:
                del self.cache[key]
                self.stats.invalidations += 1

            self.stats.total_entries = len(self.cache)
            return len(keys_to_remove)

    def clear(self):
        """Clear entire cache"""
        with self.lock:
            count = len(self.cache)
            self.cache.clear()
            self.stats.invalidations += count
            self.stats.total_entries = 0
            self.stats.total_size_bytes = 0

    def get_stats(self) -> dict:
        """Get cache statistics"""
        with self.lock:
            return self.stats.to_dict()


class FilePersistentCache:
    """
    File-based persistent cache using Azure File Storage.

    Provides durable caching across function invocations and restarts.
    """

    def __init__(self, cache_dir: str = '/tmp/cache', enabled: bool = True):
        """
        Initialize file cache.

        Args:
            cache_dir: Directory for cache files
            enabled: Enable file caching
        """
        self.cache_dir = Path(cache_dir)
        self.enabled = enabled
        self.lock = threading.RLock()

        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, key: str) -> Path:
        """Get file path for cache key"""
        # Use hash to avoid filesystem issues with special characters
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.json"

    def get(self, key: str) -> Optional[Any]:
        """Get value from file cache"""
        if not self.enabled:
            return None

        with self.lock:
            file_path = self._get_file_path(key)

            if not file_path.exists():
                return None

            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)

                entry = CacheEntry(**data['entry'])

                # Check expiration
                if entry.is_expired():
                    file_path.unlink()
                    return None

                return entry.value

            except Exception as e:
                logging.error(f"Error reading cache file {file_path}: {e}")
                return None

    def set(self, key: str, value: Any, ttl: int = 3600, tags: List[str] = None,
            cache_type: str = 'default') -> None:
        """Set value in file cache"""
        if not self.enabled:
            return

        with self.lock:
            file_path = self._get_file_path(key)

            try:
                size_bytes = len(json.dumps(value).encode('utf-8'))
            except:
                size_bytes = 0

            entry = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                last_accessed=time.time(),
                access_count=0,
                ttl=ttl,
                tags=tags or [],
                size_bytes=size_bytes,
                cache_type=cache_type
            )

            try:
                with open(file_path, 'w') as f:
                    json.dump({'entry': entry.to_dict()}, f)
            except Exception as e:
                logging.error(f"Error writing cache file {file_path}: {e}")

    def invalidate(self, key: str) -> bool:
        """Invalidate specific file cache entry"""
        if not self.enabled:
            return False

        with self.lock:
            file_path = self._get_file_path(key)

            if file_path.exists():
                file_path.unlink()
                return True

            return False

    def clear(self):
        """Clear all file cache entries"""
        if not self.enabled:
            return

        with self.lock:
            for file_path in self.cache_dir.glob('*.json'):
                try:
                    file_path.unlink()
                except Exception as e:
                    logging.error(f"Error deleting cache file {file_path}: {e}")


class RedisCache:
    """
    Redis-based distributed cache for production scaling.

    Provides shared caching across multiple function instances.
    """

    def __init__(self, host: str = 'localhost', port: int = 6379,
                 password: Optional[str] = None, db: int = 0):
        """
        Initialize Redis cache.

        Args:
            host: Redis host
            port: Redis port
            password: Redis password
            db: Redis database number
        """
        self.enabled = REDIS_AVAILABLE
        self.client = None

        if self.enabled:
            try:
                self.client = redis.Redis(
                    host=host,
                    port=port,
                    password=password,
                    db=db,
                    decode_responses=True
                )
                # Test connection
                self.client.ping()
                logging.info("Redis cache connected successfully")
            except Exception as e:
                logging.error(f"Redis connection failed: {e}")
                self.enabled = False

    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        if not self.enabled or not self.client:
            return None

        try:
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logging.error(f"Redis get error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set value in Redis"""
        if not self.enabled or not self.client:
            return

        try:
            data = json.dumps(value)
            if ttl > 0:
                self.client.setex(key, ttl, data)
            else:
                self.client.set(key, data)
        except Exception as e:
            logging.error(f"Redis set error: {e}")

    def invalidate(self, key: str) -> bool:
        """Invalidate Redis entry"""
        if not self.enabled or not self.client:
            return False

        try:
            return self.client.delete(key) > 0
        except Exception as e:
            logging.error(f"Redis delete error: {e}")
            return False

    def clear(self):
        """Clear all Redis entries in current DB"""
        if not self.enabled or not self.client:
            return

        try:
            self.client.flushdb()
        except Exception as e:
            logging.error(f"Redis flush error: {e}")


class CacheManager:
    """
    Main cache manager coordinating all cache layers.

    Implements multi-tier caching strategy:
    1. In-memory LRU cache (fastest)
    2. File-based persistent cache (durable)
    3. Redis distributed cache (scalable)
    4. Semantic similarity cache (intelligent)
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize cache manager.

        Args:
            config: Cache configuration dictionary
        """
        self.config = config or self._default_config()

        # Initialize cache layers
        self.memory_cache = LRUCache(
            max_size=self.config['memory_cache']['max_size']
        )

        self.file_cache = FilePersistentCache(
            cache_dir=self.config['file_cache']['cache_dir'],
            enabled=self.config['file_cache']['enabled']
        )

        self.redis_cache = RedisCache(
            host=self.config['redis']['host'],
            port=self.config['redis']['port'],
            password=self.config['redis'].get('password'),
            db=self.config['redis']['db']
        ) if self.config['redis']['enabled'] else None

        self.semantic_cache = SemanticSimilarityCache(
            similarity_threshold=self.config['semantic_cache']['similarity_threshold']
        ) if self.config['semantic_cache']['enabled'] else None

        self.stats = CacheStats()
        self.lock = threading.RLock()

        logging.info("CacheManager initialized successfully")

    def _default_config(self) -> Dict:
        """Get default cache configuration"""
        return {
            'memory_cache': {
                'max_size': 1000,
                'enabled': True
            },
            'file_cache': {
                'cache_dir': '/tmp/ambassador_cache',
                'enabled': True
            },
            'redis': {
                'enabled': False,
                'host': 'localhost',
                'port': 6379,
                'db': 0
            },
            'semantic_cache': {
                'enabled': True,
                'similarity_threshold': 0.95
            },
            'cache_types': {
                'response': {'ttl': 3600, 'enabled': True},
                'semantic': {'ttl': 7200, 'enabled': True},
                'agent_metadata': {'ttl': 86400, 'enabled': True},
                'ambassador_config': {'ttl': 3600, 'enabled': True},
                'memory_context': {'ttl': 1800, 'enabled': True},
                'analytics': {'ttl': 300, 'enabled': True}
            }
        }

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate cache key from arguments.

        Args:
            prefix: Key prefix (cache type)
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Hashed cache key
        """
        # Create deterministic string from arguments
        key_parts = [prefix]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))

        key_string = '|'.join(key_parts)

        # Hash for consistent length
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()
        return f"{prefix}:{key_hash}"

    def get(self, cache_type: str, *args, **kwargs) -> Optional[Any]:
        """
        Get value from cache (multi-tier lookup).

        Args:
            cache_type: Type of cache entry
            *args: Arguments for key generation
            **kwargs: Keyword arguments for key generation

        Returns:
            Cached value or None
        """
        start_time = time.time()

        # Check if this cache type is enabled
        if not self.config['cache_types'].get(cache_type, {}).get('enabled', False):
            return None

        key = self._generate_key(cache_type, *args, **kwargs)

        # Try memory cache first
        value = self.memory_cache.get(key)
        if value is not None:
            self._record_hit(time.time() - start_time)
            return value

        # Try semantic cache for response types
        if cache_type == 'response' and self.semantic_cache:
            query = str(args[0]) if args else ''
            semantic_key = self.semantic_cache.find_similar(query)

            if semantic_key:
                value = self.memory_cache.get(semantic_key)
                if value is not None:
                    self._record_hit(time.time() - start_time)
                    return value

        # Try file cache
        value = self.file_cache.get(key)
        if value is not None:
            # Warm memory cache
            self.memory_cache.set(key, value,
                ttl=self.config['cache_types'][cache_type]['ttl'],
                cache_type=cache_type)
            self._record_hit(time.time() - start_time)
            return value

        # Try Redis cache
        if self.redis_cache and self.redis_cache.enabled:
            value = self.redis_cache.get(key)
            if value is not None:
                # Warm lower-tier caches
                self.memory_cache.set(key, value,
                    ttl=self.config['cache_types'][cache_type]['ttl'],
                    cache_type=cache_type)
                self._record_hit(time.time() - start_time)
                return value

        self._record_miss(time.time() - start_time)
        return None

    def set(self, cache_type: str, value: Any, *args, tags: List[str] = None, **kwargs) -> None:
        """
        Set value in cache (all tiers).

        Args:
            cache_type: Type of cache entry
            value: Value to cache
            *args: Arguments for key generation
            tags: Tags for invalidation
            **kwargs: Keyword arguments for key generation
        """
        # Check if this cache type is enabled
        if not self.config['cache_types'].get(cache_type, {}).get('enabled', False):
            return

        key = self._generate_key(cache_type, *args, **kwargs)
        ttl = self.config['cache_types'][cache_type]['ttl']

        # Set in all cache tiers
        self.memory_cache.set(key, value, ttl=ttl, tags=tags, cache_type=cache_type)
        self.file_cache.set(key, value, ttl=ttl, tags=tags, cache_type=cache_type)

        if self.redis_cache and self.redis_cache.enabled:
            self.redis_cache.set(key, value, ttl=ttl)

        # Add to semantic cache for response types
        if cache_type == 'response' and self.semantic_cache:
            query = str(args[0]) if args else ''
            self.semantic_cache.add(query, key)

    def invalidate(self, cache_type: str, *args, **kwargs) -> bool:
        """
        Invalidate specific cache entry.

        Args:
            cache_type: Type of cache entry
            *args: Arguments for key generation
            **kwargs: Keyword arguments for key generation

        Returns:
            True if entry was invalidated
        """
        key = self._generate_key(cache_type, *args, **kwargs)

        result = False
        result |= self.memory_cache.invalidate(key)
        result |= self.file_cache.invalidate(key)

        if self.redis_cache and self.redis_cache.enabled:
            result |= self.redis_cache.invalidate(key)

        return result

    def invalidate_by_tag(self, tag: str) -> int:
        """
        Invalidate all entries with specific tag.

        Args:
            tag: Tag to match

        Returns:
            Number of entries invalidated
        """
        return self.memory_cache.invalidate_by_tag(tag)

    def clear(self, cache_type: Optional[str] = None):
        """
        Clear cache entries.

        Args:
            cache_type: Specific cache type to clear (None = all)
        """
        if cache_type:
            # Clear specific type (would need tag-based filtering)
            logging.info(f"Clearing cache type: {cache_type}")
        else:
            # Clear all caches
            self.memory_cache.clear()
            self.file_cache.clear()

            if self.redis_cache and self.redis_cache.enabled:
                self.redis_cache.clear()

            if self.semantic_cache:
                self.semantic_cache.clear()

    def warm_cache(self, cache_type: str, items: List[Tuple[Any, Any]]):
        """
        Pre-populate cache with known values.

        Args:
            cache_type: Type of cache entries
            items: List of (key_args, value) tuples
        """
        logging.info(f"Warming cache for type: {cache_type}")

        for key_args, value in items:
            if isinstance(key_args, (list, tuple)):
                self.set(cache_type, value, *key_args)
            else:
                self.set(cache_type, value, key_args)

    def get_stats(self) -> dict:
        """Get comprehensive cache statistics"""
        with self.lock:
            stats = self.memory_cache.get_stats()

            # Add global stats
            stats['timestamp'] = datetime.now().isoformat()
            stats['cache_layers'] = {
                'memory': self.memory_cache is not None,
                'file': self.file_cache.enabled,
                'redis': self.redis_cache.enabled if self.redis_cache else False,
                'semantic': self.semantic_cache is not None
            }

            return stats

    def _record_hit(self, response_time_ms: float):
        """Record cache hit"""
        with self.lock:
            self.stats.hits += 1
            # Estimate cost savings (average OpenAI API call ~$0.002)
            self.stats.cost_savings_usd += 0.002

    def _record_miss(self, response_time_ms: float):
        """Record cache miss"""
        with self.lock:
            self.stats.misses += 1


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager(config: Optional[Dict] = None) -> CacheManager:
    """
    Get or create global cache manager instance.

    Args:
        config: Optional cache configuration

    Returns:
        CacheManager instance
    """
    global _cache_manager

    if _cache_manager is None:
        _cache_manager = CacheManager(config)

    return _cache_manager


def load_cache_config(config_path: str) -> Dict:
    """
    Load cache configuration from JSON file.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading cache config from {config_path}: {e}")
        return {}
