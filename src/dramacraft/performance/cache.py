"""
缓存管理模块

提供多级缓存功能：
- 内存缓存
- Redis缓存
- 分布式缓存
- 缓存策略
"""

import asyncio
import time
import pickle
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
import json


class CacheStrategy(Enum):
    """缓存策略枚举"""
    LRU = "lru"  # 最近最少使用
    LFU = "lfu"  # 最少使用频率
    FIFO = "fifo"  # 先进先出
    TTL = "ttl"  # 基于时间


@dataclass
class CacheItem:
    """缓存项"""
    key: str
    value: Any
    created_at: datetime
    accessed_at: datetime
    access_count: int = 0
    ttl: Optional[int] = None
    
    @property
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl is None:
            return False
        return datetime.utcnow() > self.created_at + timedelta(seconds=self.ttl)
    
    def touch(self):
        """更新访问时间"""
        self.accessed_at = datetime.utcnow()
        self.access_count += 1


class MemoryCache:
    """内存缓存"""
    
    def __init__(
        self, 
        max_size: int = 1000,
        default_ttl: Optional[int] = None,
        strategy: CacheStrategy = CacheStrategy.LRU
    ):
        """初始化内存缓存"""
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.strategy = strategy
        self.cache: Dict[str, CacheItem] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        async with self._lock:
            if key not in self.cache:
                return None
            
            item = self.cache[key]
            
            # 检查过期
            if item.is_expired:
                del self.cache[key]
                return None
            
            # 更新访问信息
            item.touch()
            return item.value
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """设置缓存值"""
        async with self._lock:
            # 检查容量
            if len(self.cache) >= self.max_size and key not in self.cache:
                await self._evict()
            
            # 创建缓存项
            item = CacheItem(
                key=key,
                value=value,
                created_at=datetime.utcnow(),
                accessed_at=datetime.utcnow(),
                ttl=ttl or self.default_ttl
            )
            
            self.cache[key] = item
            return True
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        async with self._lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    async def clear(self):
        """清空缓存"""
        async with self._lock:
            self.cache.clear()
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        async with self._lock:
            if key not in self.cache:
                return False
            
            item = self.cache[key]
            if item.is_expired:
                del self.cache[key]
                return False
            
            return True
    
    async def keys(self) -> List[str]:
        """获取所有键"""
        async with self._lock:
            # 清理过期项
            expired_keys = [
                key for key, item in self.cache.items()
                if item.is_expired
            ]
            for key in expired_keys:
                del self.cache[key]
            
            return list(self.cache.keys())
    
    async def size(self) -> int:
        """获取缓存大小"""
        async with self._lock:
            return len(self.cache)
    
    async def _evict(self):
        """缓存淘汰"""
        if not self.cache:
            return
        
        if self.strategy == CacheStrategy.LRU:
            # 淘汰最近最少使用的项
            oldest_key = min(
                self.cache.keys(),
                key=lambda k: self.cache[k].accessed_at
            )
            del self.cache[oldest_key]
        
        elif self.strategy == CacheStrategy.LFU:
            # 淘汰使用频率最低的项
            least_used_key = min(
                self.cache.keys(),
                key=lambda k: self.cache[k].access_count
            )
            del self.cache[least_used_key]
        
        elif self.strategy == CacheStrategy.FIFO:
            # 淘汰最早创建的项
            oldest_key = min(
                self.cache.keys(),
                key=lambda k: self.cache[k].created_at
            )
            del self.cache[oldest_key]
        
        elif self.strategy == CacheStrategy.TTL:
            # 淘汰最早过期的项
            expired_items = [
                (key, item) for key, item in self.cache.items()
                if item.is_expired
            ]
            
            if expired_items:
                # 删除所有过期项
                for key, _ in expired_items:
                    del self.cache[key]
            else:
                # 如果没有过期项，使用LRU策略
                oldest_key = min(
                    self.cache.keys(),
                    key=lambda k: self.cache[k].accessed_at
                )
                del self.cache[oldest_key]


class RedisCache:
    """Redis缓存（模拟实现）"""
    
    def __init__(
        self, 
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        default_ttl: Optional[int] = None
    ):
        """初始化Redis缓存"""
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.default_ttl = default_ttl
        
        # 模拟Redis连接（实际应用中使用aioredis）
        self._storage: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        async with self._lock:
            if key not in self._storage:
                return None
            
            item = self._storage[key]
            
            # 检查过期
            if item.get("expires_at") and datetime.utcnow() > item["expires_at"]:
                del self._storage[key]
                return None
            
            # 反序列化值
            return pickle.loads(item["value"])
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """设置缓存值"""
        async with self._lock:
            expires_at = None
            if ttl or self.default_ttl:
                expires_at = datetime.utcnow() + timedelta(seconds=ttl or self.default_ttl)
            
            self._storage[key] = {
                "value": pickle.dumps(value),
                "created_at": datetime.utcnow(),
                "expires_at": expires_at
            }
            return True
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        async with self._lock:
            if key in self._storage:
                del self._storage[key]
                return True
            return False
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        async with self._lock:
            if key not in self._storage:
                return False
            
            item = self._storage[key]
            if item.get("expires_at") and datetime.utcnow() > item["expires_at"]:
                del self._storage[key]
                return False
            
            return True
    
    async def expire(self, key: str, ttl: int) -> bool:
        """设置过期时间"""
        async with self._lock:
            if key not in self._storage:
                return False
            
            self._storage[key]["expires_at"] = datetime.utcnow() + timedelta(seconds=ttl)
            return True
    
    async def ttl(self, key: str) -> Optional[int]:
        """获取剩余过期时间"""
        async with self._lock:
            if key not in self._storage:
                return None
            
            item = self._storage[key]
            if not item.get("expires_at"):
                return -1  # 永不过期
            
            remaining = item["expires_at"] - datetime.utcnow()
            return max(0, int(remaining.total_seconds()))
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """获取匹配的键"""
        async with self._lock:
            # 简化实现，不支持复杂模式匹配
            if pattern == "*":
                return list(self._storage.keys())
            else:
                return [key for key in self._storage.keys() if pattern in key]
    
    async def clear(self):
        """清空缓存"""
        async with self._lock:
            self._storage.clear()


class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        """初始化缓存管理器"""
        self.caches: Dict[str, Union[MemoryCache, RedisCache]] = {}
        self.default_cache: Optional[str] = None
    
    def add_cache(
        self, 
        name: str, 
        cache: Union[MemoryCache, RedisCache],
        is_default: bool = False
    ):
        """添加缓存"""
        self.caches[name] = cache
        if is_default or self.default_cache is None:
            self.default_cache = name
    
    def get_cache(self, name: Optional[str] = None) -> Optional[Union[MemoryCache, RedisCache]]:
        """获取缓存实例"""
        cache_name = name or self.default_cache
        return self.caches.get(cache_name)
    
    async def get(self, key: str, cache_name: Optional[str] = None) -> Optional[Any]:
        """获取缓存值"""
        cache = self.get_cache(cache_name)
        if cache:
            return await cache.get(key)
        return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        cache_name: Optional[str] = None
    ) -> bool:
        """设置缓存值"""
        cache = self.get_cache(cache_name)
        if cache:
            return await cache.set(key, value, ttl)
        return False
    
    async def delete(self, key: str, cache_name: Optional[str] = None) -> bool:
        """删除缓存"""
        cache = self.get_cache(cache_name)
        if cache:
            return await cache.delete(key)
        return False
    
    async def exists(self, key: str, cache_name: Optional[str] = None) -> bool:
        """检查键是否存在"""
        cache = self.get_cache(cache_name)
        if cache:
            return await cache.exists(key)
        return False
    
    async def clear(self, cache_name: Optional[str] = None):
        """清空缓存"""
        cache = self.get_cache(cache_name)
        if cache:
            await cache.clear()
    
    async def clear_all(self):
        """清空所有缓存"""
        for cache in self.caches.values():
            await cache.clear()
    
    def cache_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        # 创建一个基于参数的唯一键
        key_data = {
            "args": args,
            "kwargs": sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def cached(
        self, 
        ttl: Optional[int] = None,
        cache_name: Optional[str] = None,
        key_func: Optional[Callable] = None
    ):
        """缓存装饰器"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # 生成缓存键
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = f"{func.__name__}:{self.cache_key(*args, **kwargs)}"
                
                # 尝试从缓存获取
                cached_result = await self.get(cache_key, cache_name)
                if cached_result is not None:
                    return cached_result
                
                # 执行函数
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # 存储到缓存
                await self.set(cache_key, result, ttl, cache_name)
                
                return result
            
            return wrapper
        return decorator
    
    async def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取缓存统计信息"""
        stats = {}
        
        for name, cache in self.caches.items():
            if isinstance(cache, MemoryCache):
                stats[name] = {
                    "type": "memory",
                    "size": await cache.size(),
                    "max_size": cache.max_size,
                    "strategy": cache.strategy.value,
                    "default_ttl": cache.default_ttl
                }
            elif isinstance(cache, RedisCache):
                stats[name] = {
                    "type": "redis",
                    "host": cache.host,
                    "port": cache.port,
                    "db": cache.db,
                    "default_ttl": cache.default_ttl
                }
        
        return stats


# 全局缓存管理器实例
cache_manager = CacheManager()

# 便捷函数
async def get_cached(key: str, cache_name: Optional[str] = None) -> Optional[Any]:
    """获取缓存值"""
    return await cache_manager.get(key, cache_name)

async def set_cached(
    key: str, 
    value: Any, 
    ttl: Optional[int] = None,
    cache_name: Optional[str] = None
) -> bool:
    """设置缓存值"""
    return await cache_manager.set(key, value, ttl, cache_name)

def cached(
    ttl: Optional[int] = None,
    cache_name: Optional[str] = None,
    key_func: Optional[Callable] = None
):
    """缓存装饰器"""
    return cache_manager.cached(ttl, cache_name, key_func)
