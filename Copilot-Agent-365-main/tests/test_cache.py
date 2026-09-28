"""
Test suite for caching system

Run with: pytest tests/test_cache.py -v
"""

import os
import shutil
import sys
import tempfile
import time
from unittest.mock import patch

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import utils.cache
from utils.cache import (
    CacheManager,
    FilePersistentCache,
    LRUCache,
    RedisCache,
    SemanticSimilarityCache,
    get_cache_manager,
)
from utils.cached_openai import CachedAzureOpenAI

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_cache_dir():
    """Create temporary cache directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def lru_cache():
    """Create LRU cache instance"""
    return LRUCache(max_size=10)


@pytest.fixture
def file_cache(temp_cache_dir):
    """Create file cache instance"""
    return FilePersistentCache(cache_dir=temp_cache_dir)


@pytest.fixture
def semantic_cache():
    """Create semantic cache instance"""
    return SemanticSimilarityCache(similarity_threshold=0.95)


@pytest.fixture
def cache_manager(temp_cache_dir, monkeypatch):
    """Fresh global cache manager whose file tier writes to a temporary directory"""
    config = CacheManager._default_config(None)
    config["file_cache"]["cache_dir"] = temp_cache_dir
    monkeypatch.setattr(utils.cache, "_cache_manager", None)
    return get_cache_manager(config)


# =============================================================================
# LRU CACHE TESTS
# =============================================================================


def test_lru_cache_basic_operations(lru_cache):
    """Test basic get/set operations"""
    # Set value
    lru_cache.set("key1", "value1")

    # Get value
    assert lru_cache.get("key1") == "value1"

    # Get non-existent key
    assert lru_cache.get("key2") is None


def test_lru_cache_eviction(lru_cache):
    """Test LRU eviction when cache is full"""
    # Fill cache to max size
    for i in range(10):
        lru_cache.set(f"key{i}", f"value{i}")

    # Add one more (should evict key0)
    lru_cache.set("key10", "value10")

    # key0 should be evicted
    assert lru_cache.get("key0") is None
    assert lru_cache.get("key10") == "value10"


def test_lru_cache_ttl_expiration(lru_cache):
    """Test TTL expiration"""
    # Set with short TTL
    lru_cache.set("key1", "value1", ttl=1)

    # Should exist immediately
    assert lru_cache.get("key1") == "value1"

    # Wait for expiration
    time.sleep(1.1)

    # Should be expired
    assert lru_cache.get("key1") is None


def test_lru_cache_stats(lru_cache):
    """Test statistics tracking"""
    lru_cache.set("key1", "value1")
    lru_cache.get("key1")  # Hit
    lru_cache.get("key2")  # Miss

    stats = lru_cache.get_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["total_entries"] == 1


def test_lru_cache_tag_invalidation(lru_cache):
    """Test tag-based invalidation"""
    lru_cache.set("key1", "value1", tags=["tag1", "tag2"])
    lru_cache.set("key2", "value2", tags=["tag2"])
    lru_cache.set("key3", "value3", tags=["tag3"])

    # Invalidate by tag2
    invalidated = lru_cache.invalidate_by_tag("tag2")

    assert invalidated == 2
    assert lru_cache.get("key1") is None
    assert lru_cache.get("key2") is None
    assert lru_cache.get("key3") == "value3"


# =============================================================================
# FILE CACHE TESTS
# =============================================================================


def test_file_cache_basic_operations(file_cache):
    """Test basic file cache operations"""
    file_cache.set("key1", {"data": "value1"})
    result = file_cache.get("key1")

    assert result == {"data": "value1"}


def test_file_cache_persistence(temp_cache_dir):
    """Test cache persists across instances"""
    # Create first instance and add data
    cache1 = FilePersistentCache(cache_dir=temp_cache_dir)
    cache1.set("key1", "value1")

    # Create new instance
    cache2 = FilePersistentCache(cache_dir=temp_cache_dir)

    # Should load from the persisted cache file
    assert cache2.get("key1") == "value1"


# =============================================================================
# SEMANTIC CACHE TESTS
# =============================================================================


def test_semantic_cache_exact_match(semantic_cache):
    """Test exact query match"""
    semantic_cache.add("What is the weather?", "weather-key")
    result = semantic_cache.find_similar("What is the weather?")

    assert result == "weather-key"


def test_semantic_cache_similarity_match(semantic_cache):
    """Test similar query match"""
    embedding = np.ones(100) / 10  # unit vector
    with patch.object(semantic_cache, "_compute_embedding", return_value=embedding):
        # Add original query
        semantic_cache.add("How is the weather?", "weather-key")

        # Search with similar query (mock will return same embedding)
        result = semantic_cache.find_similar("What's the weather like?")

    # Should find match (mocked embeddings are identical)
    assert result == "weather-key"


# =============================================================================
# REDIS CACHE TESTS
# =============================================================================


def test_redis_cache_fallback():
    """Test Redis gracefully falls back when unavailable"""
    cache = RedisCache(host="invalid-host", port=6379)

    # Should be disabled but not crash
    assert cache.enabled is False
    assert cache.get("key1") is None
    cache.set("key1", "value1")  # Should not crash


# =============================================================================
# CACHE MANAGER TESTS
# =============================================================================


def test_cache_manager_singleton(cache_manager):
    """Test cache manager is singleton"""
    manager1 = get_cache_manager()
    manager2 = get_cache_manager()

    assert manager1 is manager2 is cache_manager


def test_cache_manager_tier_routing(cache_manager):
    """Test automatic tier routing"""
    # Agent metadata should go to L1
    cache_manager.set("agent_metadata", "value", "test")

    # Should be in L1 (the in-memory LRU cache)
    key = cache_manager._generate_key("agent_metadata", "test")
    assert cache_manager.memory_cache.get(key) == "value"


def test_cache_manager_invalidation(cache_manager):
    """Test tag-based invalidation across cache types"""
    # Add entries of different cache types with same tag
    cache_manager.set("response", "val1", "key1", tags=["test"])
    cache_manager.set("agent_metadata", "val2", "key2", tags=["test"])

    # Invalidate by tag (invalidate_by_tag clears the in-memory tier)
    invalidated = cache_manager.invalidate_by_tag("test")

    assert invalidated == 2
    for cache_type, arg in [("response", "key1"), ("agent_metadata", "key2")]:
        key = cache_manager._generate_key(cache_type, arg)
        assert cache_manager.memory_cache.get(key) is None


def test_cache_manager_stats(cache_manager):
    """Test aggregate statistics"""
    # Add some data
    cache_manager.set("response", "val1", "key1")
    cache_manager.get("response", "key1")

    stats = cache_manager.get_stats()

    assert set(stats["cache_layers"]) == {"memory", "file", "redis", "semantic"}
    assert stats["hits"] > 0
    assert cache_manager.stats.hits > 0


# =============================================================================
# UTILITY FUNCTION TESTS
# =============================================================================


def test_generate_cache_key(cache_manager):
    """Test cache key generation"""
    key1 = cache_manager._generate_key("response", "prompt1", "gpt-4", 0.7, 100)
    key2 = cache_manager._generate_key("response", "prompt1", "gpt-4", 0.7, 100)
    key3 = cache_manager._generate_key("response", "prompt2", "gpt-4", 0.7, 100)

    # Same inputs should generate same key
    assert key1 == key2

    # Different inputs should generate different key
    assert key1 != key3


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


def test_end_to_end_caching(cache_manager):
    """Test complete caching flow"""
    # Simulate OpenAI request
    request = ("Hello world", "gpt-4", 1.0, 100)

    # First request (miss)
    cached = cache_manager.get("response", *request)
    assert cached is None

    # Cache the response
    response = {"choices": [{"message": {"content": "Hi there!"}}]}
    cache_manager.set("response", response, *request)

    # Second request (hit)
    cached = cache_manager.get("response", *request)
    assert cached == response

    # Check stats
    assert cache_manager.stats.misses == 1
    assert cache_manager.stats.hits >= 1


def test_performance_l1_lookup_speed():
    """Test L1 cache lookup is < 1ms"""
    cache = LRUCache(max_size=1000)

    # Add data
    for i in range(1000):
        cache.set(f"key{i}", f"value{i}")

    # Time 100 lookups
    start = time.time()
    for i in range(100):
        cache.get(f"key{i}")
    elapsed = time.time() - start

    # Average should be < 1ms per lookup
    avg_time = (elapsed / 100) * 1000
    assert avg_time < 1.0, f"L1 lookup took {avg_time:.2f}ms (expected < 1ms)"


def test_thread_safety():
    """Test thread-safe operations"""
    import threading

    cache = LRUCache(max_size=1000)
    errors = []

    def worker(thread_id):
        try:
            for i in range(100):
                cache.set(f"thread{thread_id}_key{i}", f"value{i}")
                cache.get(f"thread{thread_id}_key{i}")
        except Exception as e:
            errors.append(e)

    # Run multiple threads
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # No errors should occur
    assert len(errors) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
