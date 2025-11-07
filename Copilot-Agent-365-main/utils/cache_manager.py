"""
Cache Manager - Unified interface for multi-tier caching

This module provides a high-level interface for managing all cache tiers:
- Automatic tier selection based on cache type
- Cache warming on startup
- Tag-based invalidation
- Comprehensive statistics
- Thread-safe operations

Usage:
    from utils.cache_manager import get_cache_manager

    cache_manager = get_cache_manager()

    # Get/Set
    value = cache_manager.get('my_key', CacheType.OPENAI_RESPONSE)
    cache_manager.set('my_key', value, CacheType.OPENAI_RESPONSE, ttl=3600)

    # Invalidate
    cache_manager.invalidate(tags=['ambassador_123'])

    # Stats
    stats = cache_manager.stats()
"""

import logging
import os
import json
import threading
from typing import Any, Optional, List, Dict
from datetime import datetime

from utils.cache import (
    CacheTier, CacheType, CacheConfig,
    LRUCache, FileCache, SemanticCache, RedisCache,
    BloomFilter, estimate_cost_savings
)


# =============================================================================
# CACHE MANAGER
# =============================================================================

class CacheManager:
    """Unified cache manager for all tiers"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize cache manager"""
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self.config = self._load_config()
        self.bloom = BloomFilter()

        # Initialize all cache tiers
        self.l1_cache = LRUCache(
            max_size=self.config.l1_size,
            default_ttl=self.config.l1_ttl
        )

        self.l2_cache = FileCache(
            cache_dir=os.path.join(os.getcwd(), '.cache'),
            max_size=self.config.l2_size,
            default_ttl=self.config.l2_ttl,
            compression=self.config.l2_compression
        )

        # Initialize semantic cache if OpenAI client available
        self.l3_cache = None
        try:
            from openai import AzureOpenAI
            client = AzureOpenAI(
                api_key=os.environ.get('AZURE_OPENAI_API_KEY'),
                api_version=os.environ.get('AZURE_OPENAI_API_VERSION'),
                azure_endpoint=os.environ.get('AZURE_OPENAI_ENDPOINT')
            )
            self.l3_cache = SemanticCache(
                threshold=self.config.l3_threshold,
                max_embeddings=self.config.l3_max_embeddings,
                default_ttl=self.config.l3_ttl,
                azure_openai_client=client
            )
            logging.info("Semantic cache initialized")
        except Exception as e:
            logging.warning(f"Semantic cache not available: {e}")

        # Initialize Redis cache if enabled
        self.l4_cache = None
        if self.config.redis_enabled and self.config.redis_host:
            self.l4_cache = RedisCache(
                host=self.config.redis_host,
                port=self.config.redis_port,
                default_ttl=self.config.redis_ttl
            )

        # Cache type to tier mapping
        self.type_to_tier = {
            CacheType.OPENAI_RESPONSE: CacheTier.L2_FILE,
            CacheType.SEMANTIC_RESPONSE: CacheTier.L3_SEMANTIC,
            CacheType.AMBASSADOR_CONFIG: CacheTier.L2_FILE,
            CacheType.AGENT_METADATA: CacheTier.L1_MEMORY,
            CacheType.MEMORY_CONTEXT: CacheTier.L1_MEMORY,
            CacheType.ANALYTICS: CacheTier.L2_FILE,
        }

        logging.info("Cache manager initialized")

    def _load_config(self) -> CacheConfig:
        """Load cache configuration"""
        config_path = os.path.join(os.getcwd(), 'cache_config.json')

        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config_data = json.load(f)

                # Parse tier settings
                tiers = config_data.get('tiers', {})
                redis_settings = config_data.get('redis', {})

                return CacheConfig(
                    l1_size=tiers.get('l1', {}).get('size', 1000),
                    l1_ttl=tiers.get('l1', {}).get('ttl', 300),
                    l2_size=tiers.get('l2', {}).get('size', 100000),
                    l2_ttl=tiers.get('l2', {}).get('ttl', 3600),
                    l2_compression=tiers.get('l2', {}).get('compression', True),
                    l3_threshold=tiers.get('semantic', {}).get('threshold', 0.95),
                    l3_ttl=tiers.get('semantic', {}).get('ttl', 86400),
                    l3_max_embeddings=tiers.get('semantic', {}).get('max_embeddings', 10000),
                    redis_enabled=redis_settings.get('enabled', False),
                    redis_host=redis_settings.get('host'),
                    redis_port=redis_settings.get('port', 6379),
                    redis_ttl=redis_settings.get('ttl', 3600)
                )
            except Exception as e:
                logging.error(f"Error loading cache config: {e}")

        # Return default config
        return CacheConfig()

    def _get_cache_for_type(self, cache_type: CacheType):
        """Get appropriate cache tier for type"""
        tier = self.type_to_tier.get(cache_type, CacheTier.L2_FILE)

        if tier == CacheTier.L1_MEMORY:
            return self.l1_cache
        elif tier == CacheTier.L2_FILE:
            return self.l2_cache
        elif tier == CacheTier.L3_SEMANTIC:
            return self.l3_cache if self.l3_cache else self.l2_cache
        elif tier == CacheTier.L4_REDIS:
            return self.l4_cache if self.l4_cache and self.l4_cache.enabled else self.l2_cache

        return self.l2_cache

    def get(self, key: str, cache_type: CacheType = CacheType.OPENAI_RESPONSE) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key
            cache_type: Type of cached content

        Returns:
            Cached value or None
        """
        # Fast miss detection with Bloom filter
        if not self.bloom.contains(key):
            return None

        # Try L1 first for all types (hot cache)
        value = self.l1_cache.get(key)
        if value is not None:
            return value

        # Try primary cache for this type
        cache = self._get_cache_for_type(cache_type)
        if cache:
            value = cache.get(key)
            if value is not None:
                # Promote to L1
                self.l1_cache.set(key, value, cache_type=cache_type)
                return value

        return None

    def set(self, key: str, value: Any, cache_type: CacheType = CacheType.OPENAI_RESPONSE,
            ttl: Optional[int] = None, tags: List[str] = None) -> None:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            cache_type: Type of content
            ttl: Time to live in seconds
            tags: Tags for invalidation
        """
        # Add to bloom filter
        self.bloom.add(key)

        # Always add to L1 for fast access
        self.l1_cache.set(key, value, ttl=ttl, cache_type=cache_type, tags=tags)

        # Add to primary cache
        cache = self._get_cache_for_type(cache_type)
        if cache and cache != self.l1_cache:
            if hasattr(cache, 'set'):
                cache.set(key, value, ttl=ttl, cache_type=cache_type, tags=tags)

    def delete(self, key: str, cache_type: CacheType = CacheType.OPENAI_RESPONSE) -> bool:
        """
        Delete key from cache

        Args:
            key: Cache key
            cache_type: Type of content

        Returns:
            True if deleted, False otherwise
        """
        deleted = False

        # Delete from L1
        if self.l1_cache.delete(key):
            deleted = True

        # Delete from primary cache
        cache = self._get_cache_for_type(cache_type)
        if cache and cache != self.l1_cache:
            if hasattr(cache, 'delete') and cache.delete(key):
                deleted = True

        return deleted

    def clear(self, cache_type: Optional[CacheType] = None) -> None:
        """
        Clear cache

        Args:
            cache_type: If provided, clear only this type. Otherwise clear all.
        """
        if cache_type is None:
            # Clear all caches
            self.l1_cache.clear()
            self.l2_cache.clear()
            if self.l3_cache:
                self.l3_cache.clear()
            if self.l4_cache:
                self.l4_cache.clear()
            self.bloom.clear()
            logging.info("All caches cleared")
        else:
            # Clear specific cache type
            cache = self._get_cache_for_type(cache_type)
            if cache:
                cache.clear()
                logging.info(f"Cache cleared for type: {cache_type.value}")

    def invalidate(self, tags: List[str]) -> int:
        """
        Invalidate cache entries by tags

        Args:
            tags: List of tags to invalidate

        Returns:
            Number of entries invalidated
        """
        total_invalidated = 0

        # Invalidate in all caches
        total_invalidated += self.l1_cache.invalidate_by_tags(tags)
        total_invalidated += self.l2_cache.invalidate_by_tags(tags)
        if self.l3_cache:
            total_invalidated += self.l3_cache.invalidate_by_tags(tags)

        logging.info(f"Invalidated {total_invalidated} entries with tags: {tags}")
        return total_invalidated

    def semantic_search(self, query: str) -> Optional[Any]:
        """
        Search semantic cache for similar query

        Args:
            query: Search query

        Returns:
            Cached response if similar query found
        """
        if not self.l3_cache:
            return None

        return self.l3_cache.search(query)

    def semantic_add(self, query: str, response: Any, ttl: Optional[int] = None,
                    tags: List[str] = None) -> bool:
        """
        Add to semantic cache

        Args:
            query: Original query
            response: Response to cache
            ttl: Time to live
            tags: Tags for invalidation

        Returns:
            True if added successfully
        """
        if not self.l3_cache:
            return False

        return self.l3_cache.add(query, response, ttl=ttl, tags=tags)

    def warm(self, cache_type: CacheType = None) -> Dict[str, int]:
        """
        Warm cache with frequently accessed data

        Args:
            cache_type: Type to warm, or None for all

        Returns:
            Dictionary with warming statistics
        """
        stats = {'warmed': 0, 'errors': 0}

        try:
            if cache_type is None or cache_type == CacheType.AGENT_METADATA:
                # Warm agent metadata
                stats['warmed'] += self._warm_agent_metadata()

            if cache_type is None or cache_type == CacheType.AMBASSADOR_CONFIG:
                # Warm ambassador configs
                stats['warmed'] += self._warm_ambassador_configs()

            logging.info(f"Cache warming complete: {stats}")
        except Exception as e:
            logging.error(f"Error warming cache: {e}")
            stats['errors'] += 1

        return stats

    def _warm_agent_metadata(self) -> int:
        """Warm agent metadata cache"""
        warmed = 0
        try:
            # Load agents from folder
            agents_dir = os.path.join(os.getcwd(), 'agents')
            if os.path.exists(agents_dir):
                for filename in os.listdir(agents_dir):
                    if filename.endswith('_agent.py'):
                        # Cache agent metadata
                        key = f"agent_metadata:{filename}"
                        # In real implementation, load actual metadata
                        self.set(key, {'filename': filename}, CacheType.AGENT_METADATA)
                        warmed += 1
        except Exception as e:
            logging.error(f"Error warming agent metadata: {e}")

        return warmed

    def _warm_ambassador_configs(self) -> int:
        """Warm ambassador config cache"""
        warmed = 0
        try:
            # Load from Azure File Storage
            from utils.azure_file_storage import AzureFileStorageManager
            storage = AzureFileStorageManager()

            # List ambassador configs
            files = storage.list_files('ambassadors')
            for file in files:
                if file.name.endswith('.json'):
                    config = storage.read_file('ambassadors', file.name)
                    if config:
                        key = f"ambassador_config:{file.name}"
                        self.set(key, config, CacheType.AMBASSADOR_CONFIG)
                        warmed += 1
        except Exception as e:
            logging.error(f"Error warming ambassador configs: {e}")

        return warmed

    def stats(self) -> Dict:
        """
        Get comprehensive cache statistics

        Returns:
            Dictionary with stats from all tiers
        """
        stats = {
            'timestamp': datetime.utcnow().isoformat(),
            'tiers': {}
        }

        # L1 stats
        l1_stats = self.l1_cache.get_stats()
        stats['tiers']['l1_memory'] = l1_stats

        # L2 stats
        l2_stats = self.l2_cache.get_stats()
        stats['tiers']['l2_file'] = l2_stats

        # L3 stats
        if self.l3_cache:
            l3_stats = self.l3_cache.get_stats()
            stats['tiers']['l3_semantic'] = l3_stats

        # L4 stats
        if self.l4_cache:
            l4_stats = self.l4_cache.get_stats()
            stats['tiers']['l4_redis'] = l4_stats

        # Aggregate stats
        total_hits = sum(tier.get('hits', 0) for tier in stats['tiers'].values())
        total_misses = sum(tier.get('misses', 0) for tier in stats['tiers'].values())
        total_items = sum(tier.get('total_items', 0) for tier in stats['tiers'].values())
        total_size = sum(tier.get('total_size_bytes', 0) for tier in stats['tiers'].values())

        stats['aggregate'] = {
            'total_hits': total_hits,
            'total_misses': total_misses,
            'total_items': total_items,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'hit_rate_percent': round((total_hits / (total_hits + total_misses) * 100)
                                     if (total_hits + total_misses) > 0 else 0, 2),
            'cost_savings_usd': round(estimate_cost_savings(total_hits), 2)
        }

        return stats

    def health_check(self) -> Dict:
        """
        Check health of all cache tiers

        Returns:
            Health status dictionary
        """
        health = {
            'healthy': True,
            'tiers': {}
        }

        # Check L1
        try:
            test_key = '__health_check__'
            self.l1_cache.set(test_key, 'ok')
            assert self.l1_cache.get(test_key) == 'ok'
            self.l1_cache.delete(test_key)
            health['tiers']['l1_memory'] = {'status': 'healthy'}
        except Exception as e:
            health['healthy'] = False
            health['tiers']['l1_memory'] = {'status': 'unhealthy', 'error': str(e)}

        # Check L2
        try:
            test_key = '__health_check__'
            self.l2_cache.set(test_key, 'ok')
            assert self.l2_cache.get(test_key) == 'ok'
            self.l2_cache.delete(test_key)
            health['tiers']['l2_file'] = {'status': 'healthy'}
        except Exception as e:
            health['healthy'] = False
            health['tiers']['l2_file'] = {'status': 'unhealthy', 'error': str(e)}

        # Check L3
        if self.l3_cache:
            health['tiers']['l3_semantic'] = {
                'status': 'healthy' if self.l3_cache.client else 'unavailable'
            }

        # Check L4
        if self.l4_cache:
            health['tiers']['l4_redis'] = {
                'status': 'healthy' if self.l4_cache.enabled else 'unavailable'
            }

        return health


# =============================================================================
# SINGLETON ACCESSOR
# =============================================================================

_cache_manager_instance = None

def get_cache_manager() -> CacheManager:
    """Get singleton cache manager instance"""
    global _cache_manager_instance
    if _cache_manager_instance is None:
        _cache_manager_instance = CacheManager()
    return _cache_manager_instance
