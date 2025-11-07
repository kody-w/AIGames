"""
Test suite for caching system

Run with: pytest tests/test_cache.py -v
"""

import pytest
import time
import os
import tempfile
import shutil
from unittest.mock import Mock, patch

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.cache import (
    LRUCache, FileCache, SemanticCache, RedisCache,
    BloomFilter, CacheType, generate_cache_key,
    estimate_cost_savings
)
from utils.cache_manager import CacheManager, get_cache_manager
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
    return LRUCache(max_size=10, default_ttl=60)


@pytest.fixture
def file_cache(temp_cache_dir):
    """Create file cache instance"""
    return FileCache(cache_dir=temp_cache_dir, max_size=100, default_ttl=60)


@pytest.fixture
def mock_openai_client():
    """Create mock OpenAI client"""
    mock = Mock()
    mock.embeddings.create.return_value.data = [Mock(embedding=[0.1] * 1536)]
    return mock


@pytest.fixture
def semantic_cache(mock_openai_client):
    """Create semantic cache instance"""
    return SemanticCache(threshold=0.95, azure_openai_client=mock_openai_client)


# =============================================================================
# LRU CACHE TESTS
# =============================================================================

def test_lru_cache_basic_operations(lru_cache):
    """Test basic get/set operations"""
    # Set value
    lru_cache.set('key1', 'value1')
    
    # Get value
    assert lru_cache.get('key1') == 'value1'
    
    # Get non-existent key
    assert lru_cache.get('key2') is None


def test_lru_cache_eviction(lru_cache):
    """Test LRU eviction when cache is full"""
    # Fill cache to max size
    for i in range(10):
        lru_cache.set(f'key{i}', f'value{i}')
    
    # Add one more (should evict key0)
    lru_cache.set('key10', 'value10')
    
    # key0 should be evicted
    assert lru_cache.get('key0') is None
    assert lru_cache.get('key10') == 'value10'


def test_lru_cache_ttl_expiration(lru_cache):
    """Test TTL expiration"""
    # Set with short TTL
    lru_cache.set('key1', 'value1', ttl=1)
    
    # Should exist immediately
    assert lru_cache.get('key1') == 'value1'
    
    # Wait for expiration
    time.sleep(1.1)
    
    # Should be expired
    assert lru_cache.get('key1') is None


def test_lru_cache_stats(lru_cache):
    """Test statistics tracking"""
    lru_cache.set('key1', 'value1')
    lru_cache.get('key1')  # Hit
    lru_cache.get('key2')  # Miss
    
    stats = lru_cache.get_stats()
    assert stats['hits'] == 1
    assert stats['misses'] == 1
    assert stats['total_items'] == 1


def test_lru_cache_tag_invalidation(lru_cache):
    """Test tag-based invalidation"""
    lru_cache.set('key1', 'value1', tags=['tag1', 'tag2'])
    lru_cache.set('key2', 'value2', tags=['tag2'])
    lru_cache.set('key3', 'value3', tags=['tag3'])
    
    # Invalidate by tag2
    invalidated = lru_cache.invalidate_by_tags(['tag2'])
    
    assert invalidated == 2
    assert lru_cache.get('key1') is None
    assert lru_cache.get('key2') is None
    assert lru_cache.get('key3') == 'value3'


# =============================================================================
# FILE CACHE TESTS
# =============================================================================

def test_file_cache_basic_operations(file_cache):
    """Test basic file cache operations"""
    file_cache.set('key1', {'data': 'value1'})
    result = file_cache.get('key1')
    
    assert result == {'data': 'value1'}


def test_file_cache_compression(file_cache):
    """Test compression is working"""
    large_data = 'x' * 10000
    file_cache.set('key1', large_data)
    
    # Get file path and check it's compressed
    file_path = file_cache._get_file_path('key1')
    uncompressed_size = len(large_data)
    compressed_size = os.path.getsize(file_path)
    
    # Compressed should be smaller
    assert compressed_size < uncompressed_size


def test_file_cache_persistence(temp_cache_dir):
    """Test cache persists across instances"""
    # Create first instance and add data
    cache1 = FileCache(cache_dir=temp_cache_dir)
    cache1.set('key1', 'value1')
    
    # Create new instance
    cache2 = FileCache(cache_dir=temp_cache_dir)
    
    # Should load from persisted index
    assert cache2.get('key1') == 'value1'


def test_file_cache_eviction(file_cache):
    """Test eviction when full"""
    # Fill cache
    for i in range(100):
        file_cache.set(f'key{i}', f'value{i}')
    
    # Add one more
    file_cache.set('key100', 'value100')
    
    # Oldest should be evicted
    stats = file_cache.get_stats()
    assert stats['evictions'] >= 1


# =============================================================================
# SEMANTIC CACHE TESTS
# =============================================================================

def test_semantic_cache_exact_match(semantic_cache):
    """Test exact query match"""
    semantic_cache.add("What is the weather?", "It's sunny")
    result = semantic_cache.search("What is the weather?")
    
    assert result == "It's sunny"


def test_semantic_cache_similarity_match(semantic_cache):
    """Test similar query match"""
    # Add original query
    semantic_cache.add("How is the weather?", "It's sunny")
    
    # Search with similar query (mock will return same embedding)
    result = semantic_cache.search("What's the weather like?")
    
    # Should find match (mocked embeddings are identical)
    assert result == "It's sunny"


def test_semantic_cache_no_client(semantic_cache):
    """Test graceful degradation without client"""
    cache = SemanticCache(threshold=0.95, azure_openai_client=None)
    
    # Should not crash
    assert cache.search("query") is None
    assert cache.add("query", "response") is False


# =============================================================================
# REDIS CACHE TESTS
# =============================================================================

def test_redis_cache_fallback():
    """Test Redis gracefully falls back when unavailable"""
    cache = RedisCache(host="invalid-host", port=6379)
    
    # Should be disabled but not crash
    assert cache.enabled is False
    assert cache.get('key1') is None
    cache.set('key1', 'value1')  # Should not crash


# =============================================================================
# BLOOM FILTER TESTS
# =============================================================================

def test_bloom_filter_operations():
    """Test bloom filter add/contains"""
    bloom = BloomFilter(size=1000, num_hashes=3)
    
    # Add keys
    bloom.add('key1')
    bloom.add('key2')
    
    # Should contain added keys
    assert bloom.contains('key1') is True
    assert bloom.contains('key2') is True
    
    # May have false positives, but should not have false negatives
    # (can't test negative case due to false positives)


# =============================================================================
# CACHE MANAGER TESTS
# =============================================================================

def test_cache_manager_singleton():
    """Test cache manager is singleton"""
    manager1 = get_cache_manager()
    manager2 = get_cache_manager()
    
    assert manager1 is manager2


def test_cache_manager_tier_routing():
    """Test automatic tier routing"""
    manager = get_cache_manager()
    
    # Agent metadata should go to L1
    manager.set('test', 'value', CacheType.AGENT_METADATA)
    
    # Should be in L1
    assert manager.l1_cache.get('test') == 'value'


def test_cache_manager_invalidation():
    """Test tag-based invalidation across tiers"""
    manager = get_cache_manager()
    
    # Add to multiple tiers with same tag
    manager.set('key1', 'val1', CacheType.OPENAI_RESPONSE, tags=['test'])
    manager.set('key2', 'val2', CacheType.AGENT_METADATA, tags=['test'])
    
    # Invalidate by tag
    invalidated = manager.invalidate(['test'])
    
    assert invalidated >= 2


def test_cache_manager_stats():
    """Test aggregate statistics"""
    manager = get_cache_manager()
    
    # Add some data
    manager.set('key1', 'val1', CacheType.OPENAI_RESPONSE)
    manager.get('key1', CacheType.OPENAI_RESPONSE)
    
    stats = manager.stats()
    
    assert 'aggregate' in stats
    assert 'tiers' in stats
    assert stats['aggregate']['total_hits'] > 0


# =============================================================================
# UTILITY FUNCTION TESTS
# =============================================================================

def test_generate_cache_key():
    """Test cache key generation"""
    key1 = generate_cache_key("prompt1", "gpt-4", 0.7, 100)
    key2 = generate_cache_key("prompt1", "gpt-4", 0.7, 100)
    key3 = generate_cache_key("prompt2", "gpt-4", 0.7, 100)
    
    # Same inputs should generate same key
    assert key1 == key2
    
    # Different inputs should generate different key
    assert key1 != key3


def test_estimate_cost_savings():
    """Test cost savings calculation"""
    savings = estimate_cost_savings(
        cache_hits=1000,
        tokens_per_request=1000,
        cost_per_1k_tokens=0.01
    )
    
    # 1000 hits * 1000 tokens = 1,000,000 tokens
    # 1,000,000 / 1000 * 0.01 = $10
    assert savings == 10.0


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

def test_end_to_end_caching():
    """Test complete caching flow"""
    manager = get_cache_manager()
    
    # Simulate OpenAI request
    cache_key = generate_cache_key("Hello world", "gpt-4", 1.0, 100)
    
    # First request (miss)
    cached = manager.get(cache_key, CacheType.OPENAI_RESPONSE)
    assert cached is None
    
    # Cache the response
    response = {"choices": [{"message": {"content": "Hi there!"}}]}
    manager.set(cache_key, response, CacheType.OPENAI_RESPONSE, ttl=3600)
    
    # Second request (hit)
    cached = manager.get(cache_key, CacheType.OPENAI_RESPONSE)
    assert cached == response
    
    # Check stats
    stats = manager.stats()
    assert stats['aggregate']['total_hits'] >= 1


def test_performance_l1_lookup_speed():
    """Test L1 cache lookup is < 1ms"""
    cache = LRUCache(max_size=1000)
    
    # Add data
    for i in range(1000):
        cache.set(f'key{i}', f'value{i}')
    
    # Time 100 lookups
    start = time.time()
    for i in range(100):
        cache.get(f'key{i}')
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
                cache.set(f'thread{thread_id}_key{i}', f'value{i}')
                cache.get(f'thread{thread_id}_key{i}')
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


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
