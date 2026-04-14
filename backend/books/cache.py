"""
Redis caching layer for Document Intelligence Platform
Provides persistent caching with automatic serialization.
"""
import os
import json
import hashlib
import logging
from typing import Any, Optional, Callable
from functools import wraps
from django.conf import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Redis-based caching with automatic serialization and TTL support.
    Falls back to in-memory cache if Redis is unavailable.
    """
    
    def __init__(self):
        self._client = None
        self._fallback_cache = {}
        self._use_fallback = False
        
    def _get_client(self):
        """Lazy initialization of Redis client."""
        if self._client is None:
            try:
                import redis
                redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
                self._client = redis.from_url(redis_url, decode_responses=True)
                self._client.ping()
                self._use_fallback = False
                logger.info("Redis cache connected successfully")
            except Exception as e:
                logger.warning(f"Redis not available, using in-memory fallback: {e}")
                self._client = None
                self._use_fallback = True
        return self._client if not self._use_fallback else None
    
    @property
    def client(self):
        return self._get_client()
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a cache key from prefix and arguments."""
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from cache."""
        try:
            if self.client:
                value = self.client.get(key)
                if value:
                    return json.loads(value)
            else:
                return self._fallback_cache.get(key, default)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        return default
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set a value in cache with TTL."""
        try:
            serialized = json.dumps(value, default=str)
            if self.client:
                self.client.setex(key, ttl, serialized)
            else:
                self._fallback_cache[key] = serialized
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        try:
            if self.client:
                self.client.delete(key)
            else:
                self._fallback_cache.pop(key, None)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        try:
            if self.client:
                return bool(self.client.exists(key))
            else:
                return key in self._fallback_cache
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return False
    
    def clear_prefix(self, prefix: str) -> int:
        """Clear all keys with a given prefix."""
        try:
            if self.client:
                keys = self.client.keys(f"{prefix}:*")
                if keys:
                    return self.client.delete(*keys)
            else:
                keys_to_delete = [k for k in self._fallback_cache if k.startswith(prefix)]
                for k in keys_to_delete:
                    del self._fallback_cache[k]
                return len(keys_to_delete)
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
        return 0
    
    def ping(self) -> bool:
        """Check if Redis is available."""
        try:
            if self.client:
                self.client.ping()
                return True
        except Exception:
            pass
        return False
    
    def stats(self) -> dict:
        """Get cache statistics."""
        try:
            if self.client:
                info = self.client.info('memory')
                return {
                    'used_memory': info.get('used_memory_human', 'unknown'),
                    'connected': True
                }
            else:
                return {
                    'used_memory': f"{len(self._fallback_cache)} keys",
                    'connected': False
                }
        except Exception as e:
            return {'error': str(e)}


class CachedFunction:
    """
    Decorator for caching function results with Redis.
    """
    
    def __init__(self, prefix: str, ttl: int = 3600):
        self.prefix = prefix
        self.ttl = ttl
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = redis_cache
            key = cache._generate_key(self.prefix, *args, **kwargs)
            
            # Try to get from cache
            cached = cache.get(key)
            if cached is not None:
                return cached
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(key, result, self.ttl)
            
            return result
        
        return wrapper


# Global cache instance
redis_cache = RedisCache()


def cached(prefix: str, ttl: int = 3600):
    """
    Decorator to cache function results.
    
    Usage:
        @cached('book_summary', ttl=1800)
        def get_book_summary(book_id):
            ...
    """
    return CachedFunction(prefix, ttl)


def invalidate_cache(prefix: str, *args, **kwargs):
    """
    Invalidate a specific cache entry.
    
    Usage:
        invalidate_cache('book_summary', book_id=123)
    """
    key = redis_cache._generate_key(prefix, *args, **kwargs)
    redis_cache.delete(key)


def clear_cache_prefix(prefix: str):
    """Clear all cache entries with a prefix."""
    return redis_cache.clear_prefix(prefix)
