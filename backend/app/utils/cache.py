import redis
import json
import hashlib
from typing import Any, Optional
from datetime import timedelta
 
class CacheService:
    """Redis cache service for search results"""
    
    def __init__(self, redis_url: str):
        """Initialize Redis connection"""
        self.redis_client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=5
        )
        self.default_ttl = 3600  # 1 hour
    
    def _generate_cache_key(self, prefix: str, query: str, **kwargs) -> str:
        """Generate a unique cache key from query and parameters"""
        # Create a string from query and kwargs
        key_parts = [prefix, query]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        
        key_string = "|".join(key_parts)
        
        # Hash for consistent length
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    async def get_search_results(self, query: str, limit: int = 20) -> Optional[dict]:
        """Get cached search results"""
        try:
            cache_key = self._generate_cache_key("search", query, limit=limit)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                return json.loads(cached_data)
            return None
            
        except Exception as e:
            print(f"Cache get error: {str(e)}")
            return None
    
    async def set_search_results(
        self, 
        query: str, 
        results: dict, 
        limit: int = 20,
        ttl: Optional[int] = None
    ) -> bool:
        """Cache search results"""
        try:
            cache_key = self._generate_cache_key("search", query, limit=limit)
            ttl = ttl or self.default_ttl
            
            self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(results)
            )
            return True
            
        except Exception as e:
            print(f"Cache set error: {str(e)}")
            return False
    
    async def invalidate_search(self, query: str, limit: int = 20) -> bool:
        """Invalidate specific search cache"""
        try:
            cache_key = self._generate_cache_key("search", query, limit=limit)
            self.redis_client.delete(cache_key)
            return True
        except Exception as e:
            print(f"Cache invalidate error: {str(e)}")
            return False
    
    async def clear_all(self) -> bool:
        """Clear all cache (use with caution)"""
        try:
            self.redis_client.flushdb()
            return True
        except Exception as e:
            print(f"Cache clear error: {str(e)}")
            return False
    
    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        try:
            self.redis_client.ping()
            return True
        except Exception:
            return False
