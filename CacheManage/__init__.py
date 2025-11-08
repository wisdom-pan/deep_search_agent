from .strategies import (
    CacheKeyStrategy,
    SimpleCacheKeyStrategy,
    ContextAwareCacheKeyStrategy,
    ContextAndKeywordAwareCacheKeyStrategy
)

from .backends import (
    CacheStorageBackend,
    MemoryCacheBackend,
    DiskCacheBackend,
    HybridCacheBackend,
    ThreadSafeCacheBackend
)

from .models import CacheItem
from .manager import CacheManager
# from .vector_similarity import VectorSimilarityMatcher  # Not used - using Neo4j vector search instead

__all__ = [
    # Key strategies
    'CacheKeyStrategy',
    'SimpleCacheKeyStrategy',
    'ContextAwareCacheKeyStrategy',
    'ContextAndKeywordAwareCacheKeyStrategy',

    # Storage backends
    'CacheStorageBackend',
    'MemoryCacheBackend',
    'DiskCacheBackend',
    'HybridCacheBackend',
    'ThreadSafeCacheBackend',

    # Models
    'CacheItem',

    # Main manager
    'CacheManager',

    # Vector similarity - deprecated
    # 'VectorSimilarityMatcher'
]