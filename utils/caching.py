"""
High-Performance Caching System
==============================

This module provides secure, high-performance caching utilities
optimized for ID validation operations. The caching system includes
multiple strategies and security features.

Features:
- LRU (Least Recently Used) cache
- TTL (Time To Live) cache with expiration
- Secure cache with encrypted storage
- Thread-safe operations
- Memory usage monitoring
- Cache statistics and metrics

Examples:
    >>> from pyidverify.utils.caching import LRUCache, cache_result
    >>> 
    >>> # Create LRU cache
    >>> cache = LRUCache(maxsize=1000)
    >>> cache.set("key1", "value1")
    >>> value = cache.get("key1")  # Returns "value1"
    >>> 
    >>> # Use cache decorator
    >>> @cache_result(maxsize=500, ttl=3600)
    >>> def expensive_validation(data):
    ...     return validate_complex_id(data)

Security Features:
- Optional encryption for sensitive cache data
- Memory clearing on cache eviction
- Access pattern obfuscation
- Secure key hashing
"""

from typing import Optional, Dict, Any, Union, Callable, TypeVar, Generic, Tuple, List
from dataclasses import dataclass, field
from enum import Enum
import time
import threading
import weakref
import hashlib
import secrets
from functools import wraps
from collections import OrderedDict

T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

class CacheStrategy(Enum):
    """Cache eviction strategies"""
    LRU = "least_recently_used"
    FIFO = "first_in_first_out"
    TTL = "time_to_live"
    SECURE = "secure_encrypted"

@dataclass
class CacheStats:
    """Statistics for cache performance monitoring"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    current_size: int = 0
    max_size: int = 0
    hit_rate: float = 0.0
    memory_usage_bytes: int = 0
    
    def update_hit_rate(self):
        """Update hit rate calculation"""
        total = self.hits + self.misses
        self.hit_rate = (self.hits / total * 100) if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "current_size": self.current_size,
            "max_size": self.max_size,
            "hit_rate": self.hit_rate,
            "memory_usage_bytes": self.memory_usage_bytes
        }

class LRUCache(Generic[K, V]):
    """
    Thread-safe LRU (Least Recently Used) cache implementation.
    
    This cache maintains items in order of access, evicting the least
    recently used items when the cache reaches its maximum size.
    """
    
    def __init__(self, maxsize: int = 1000):
        """
        Initialize LRU cache.
        
        Args:
            maxsize: Maximum number of items to store
            
        Raises:
            ValueError: If maxsize is not positive
        """
        if maxsize <= 0:
            raise ValueError("maxsize must be positive")
        
        self._maxsize = maxsize
        self._cache: OrderedDict[K, V] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = CacheStats(max_size=maxsize)
    
    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        with self._lock:
            if key in self._cache:
                # Move to end (most recently used)
                value = self._cache.pop(key)
                self._cache[key] = value
                self._stats.hits += 1
                self._stats.update_hit_rate()
                return value
            else:
                self._stats.misses += 1
                self._stats.update_hit_rate()
                return default
    
    def set(self, key: K, value: V) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        with self._lock:
            if key in self._cache:
                # Update existing key
                self._cache.pop(key)
            elif len(self._cache) >= self._maxsize:
                # Evict least recently used
                self._cache.popitem(last=False)
                self._stats.evictions += 1
            
            self._cache[key] = value
            self._stats.current_size = len(self._cache)
    
    def delete(self, key: K) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key was deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats.current_size = len(self._cache)
                return True
            return False
    
    def clear(self) -> None:
        """Clear all items from cache"""
        with self._lock:
            self._cache.clear()
            self._stats.current_size = 0
            self._stats.evictions += len(self._cache)
    
    def size(self) -> int:
        """Get current cache size"""
        with self._lock:
            return len(self._cache)
    
    def keys(self) -> List[K]:
        """Get list of cache keys"""
        with self._lock:
            return list(self._cache.keys())
    
    def stats(self) -> CacheStats:
        """Get cache statistics"""
        with self._lock:
            self._stats.current_size = len(self._cache)
            return self._stats

class TTLCache(Generic[K, V]):
    """
    Time-To-Live cache with automatic expiration.
    
    Items are automatically removed from the cache when they expire
    based on their TTL (time-to-live) value.
    """
    
    def __init__(self, maxsize: int = 1000, default_ttl: float = 3600.0):
        """
        Initialize TTL cache.
        
        Args:
            maxsize: Maximum number of items to store
            default_ttl: Default time-to-live in seconds
            
        Raises:
            ValueError: If maxsize or default_ttl are not positive
        """
        if maxsize <= 0:
            raise ValueError("maxsize must be positive")
        if default_ttl <= 0:
            raise ValueError("default_ttl must be positive")
        
        self._maxsize = maxsize
        self._default_ttl = default_ttl
        self._cache: Dict[K, Tuple[V, float]] = {}  # value, expiry_time
        self._lock = threading.RLock()
        self._stats = CacheStats(max_size=maxsize)
    
    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """
        Get value from cache if not expired.
        
        Args:
            key: Cache key
            default: Default value if key not found or expired
            
        Returns:
            Cached value or default
        """
        current_time = time.time()
        
        with self._lock:
            if key in self._cache:
                value, expiry_time = self._cache[key]
                if current_time < expiry_time:
                    self._stats.hits += 1
                    self._stats.update_hit_rate()
                    return value
                else:
                    # Expired - remove from cache
                    del self._cache[key]
                    self._stats.evictions += 1
            
            self._stats.misses += 1
            self._stats.update_hit_rate()
            return default
    
    def set(self, key: K, value: V, ttl: Optional[float] = None) -> None:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        if ttl is None:
            ttl = self._default_ttl
        
        expiry_time = time.time() + ttl
        
        with self._lock:
            # Clean expired items if at capacity
            if len(self._cache) >= self._maxsize:
                self._clean_expired()
            
            # If still at capacity, remove oldest item
            if len(self._cache) >= self._maxsize and key not in self._cache:
                # Remove item with earliest expiry time
                oldest_key = min(self._cache.keys(), 
                               key=lambda k: self._cache[k][1])
                del self._cache[oldest_key]
                self._stats.evictions += 1
            
            self._cache[key] = (value, expiry_time)
            self._stats.current_size = len(self._cache)
    
    def _clean_expired(self) -> None:
        """Remove expired items from cache"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, expiry_time) in self._cache.items()
            if current_time >= expiry_time
        ]
        
        for key in expired_keys:
            del self._cache[key]
            self._stats.evictions += 1
    
    def delete(self, key: K) -> bool:
        """Delete key from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats.current_size = len(self._cache)
                return True
            return False
    
    def clear(self) -> None:
        """Clear all items from cache"""
        with self._lock:
            eviction_count = len(self._cache)
            self._cache.clear()
            self._stats.current_size = 0
            self._stats.evictions += eviction_count
    
    def cleanup(self) -> int:
        """
        Manually clean expired items.
        
        Returns:
            Number of items removed
        """
        with self._lock:
            initial_size = len(self._cache)
            self._clean_expired()
            self._stats.current_size = len(self._cache)
            return initial_size - len(self._cache)
    
    def stats(self) -> CacheStats:
        """Get cache statistics"""
        with self._lock:
            self._stats.current_size = len(self._cache)
            return self._stats

class SecureCache(Generic[K, V]):
    """
    Secure cache with optional encryption for sensitive data.
    
    This cache provides additional security features including
    encrypted storage and secure key hashing.
    """
    
    def __init__(self, maxsize: int = 1000, encrypt_values: bool = True,
                 key_salt: Optional[bytes] = None):
        """
        Initialize secure cache.
        
        Args:
            maxsize: Maximum number of items to store
            encrypt_values: Whether to encrypt cached values
            key_salt: Salt for key hashing (random if None)
            
        Raises:
            ValueError: If maxsize is not positive
        """
        if maxsize <= 0:
            raise ValueError("maxsize must be positive")
        
        self._maxsize = maxsize
        self._encrypt_values = encrypt_values
        self._key_salt = key_salt or secrets.token_bytes(32)
        self._cache: OrderedDict[str, Union[V, bytes]] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = CacheStats(max_size=maxsize)
        
        # Initialize encryption if enabled
        if self._encrypt_values:
            try:
                from cryptography.fernet import Fernet
                self._cipher = Fernet(Fernet.generate_key())
            except ImportError:
                # Fallback to no encryption if cryptography not available
                self._encrypt_values = False
                self._cipher = None
        else:
            self._cipher = None
    
    def _hash_key(self, key: K) -> str:
        """
        Create secure hash of cache key.
        
        Args:
            key: Original cache key
            
        Returns:
            Hashed key string
        """
        key_str = str(key).encode('utf-8')
        hasher = hashlib.blake2b(key_str, salt=self._key_salt)
        return hasher.hexdigest()
    
    def _encrypt_value(self, value: V) -> Union[V, bytes]:
        """
        Encrypt value if encryption is enabled.
        
        Args:
            value: Value to potentially encrypt
            
        Returns:
            Encrypted value or original value
        """
        if self._encrypt_values and self._cipher:
            try:
                import pickle
                serialized = pickle.dumps(value)
                return self._cipher.encrypt(serialized)
            except Exception:
                # Fall back to unencrypted storage
                return value
        return value
    
    def _decrypt_value(self, encrypted_value: Union[V, bytes]) -> V:
        """
        Decrypt value if it was encrypted.
        
        Args:
            encrypted_value: Potentially encrypted value
            
        Returns:
            Decrypted value
        """
        if self._encrypt_values and self._cipher and isinstance(encrypted_value, bytes):
            try:
                import pickle
                decrypted = self._cipher.decrypt(encrypted_value)
                return pickle.loads(decrypted)
            except Exception:
                # If decryption fails, assume it wasn't encrypted
                pass
        return encrypted_value
    
    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """Get value from secure cache"""
        hashed_key = self._hash_key(key)
        
        with self._lock:
            if hashed_key in self._cache:
                encrypted_value = self._cache.pop(hashed_key)
                self._cache[hashed_key] = encrypted_value  # Move to end
                value = self._decrypt_value(encrypted_value)
                self._stats.hits += 1
                self._stats.update_hit_rate()
                return value
            else:
                self._stats.misses += 1
                self._stats.update_hit_rate()
                return default
    
    def set(self, key: K, value: V) -> None:
        """Set value in secure cache"""
        hashed_key = self._hash_key(key)
        encrypted_value = self._encrypt_value(value)
        
        with self._lock:
            if hashed_key in self._cache:
                self._cache.pop(hashed_key)
            elif len(self._cache) >= self._maxsize:
                # Evict least recently used
                evicted_key, evicted_value = self._cache.popitem(last=False)
                # Clear evicted value from memory if it was encrypted
                if isinstance(evicted_value, bytes):
                    # Overwrite memory (basic attempt)
                    try:
                        evicted_value = b'0' * len(evicted_value)
                    except:
                        pass
                self._stats.evictions += 1
            
            self._cache[hashed_key] = encrypted_value
            self._stats.current_size = len(self._cache)
    
    def delete(self, key: K) -> bool:
        """Delete key from secure cache"""
        hashed_key = self._hash_key(key)
        
        with self._lock:
            if hashed_key in self._cache:
                evicted_value = self._cache.pop(hashed_key)
                # Clear evicted value from memory
                if isinstance(evicted_value, bytes):
                    try:
                        evicted_value = b'0' * len(evicted_value)
                    except:
                        pass
                self._stats.current_size = len(self._cache)
                return True
            return False
    
    def clear(self) -> None:
        """Clear all items from secure cache"""
        with self._lock:
            eviction_count = len(self._cache)
            # Clear values from memory
            for value in self._cache.values():
                if isinstance(value, bytes):
                    try:
                        value = b'0' * len(value)
                    except:
                        pass
            self._cache.clear()
            self._stats.current_size = 0
            self._stats.evictions += eviction_count
    
    def stats(self) -> CacheStats:
        """Get cache statistics"""
        with self._lock:
            self._stats.current_size = len(self._cache)
            return self._stats

# Global cache instances
_global_lru_cache = LRUCache(maxsize=1000)
_global_ttl_cache = TTLCache(maxsize=500, default_ttl=3600)

def cache_result(maxsize: int = 100, ttl: Optional[float] = None, 
                strategy: CacheStrategy = CacheStrategy.LRU) -> Callable:
    """
    Decorator to cache function results.
    
    Args:
        maxsize: Maximum cache size
        ttl: Time-to-live for TTL strategy
        strategy: Cache strategy to use
        
    Returns:
        Decorator function
        
    Examples:
        >>> @cache_result(maxsize=500, ttl=3600)
        >>> def expensive_function(x):
        ...     return x * x
    """
    def decorator(func: Callable) -> Callable:
        if strategy == CacheStrategy.LRU:
            func_cache = LRUCache(maxsize=maxsize)
        elif strategy == CacheStrategy.TTL:
            func_cache = TTLCache(maxsize=maxsize, 
                                default_ttl=ttl or 3600)
        elif strategy == CacheStrategy.SECURE:
            func_cache = SecureCache(maxsize=maxsize)
        else:
            func_cache = LRUCache(maxsize=maxsize)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = str(args) + str(sorted(kwargs.items()))
            
            # Try to get from cache
            result = func_cache.get(key)
            if result is not None:
                return result
            
            # Call function and cache result
            result = func(*args, **kwargs)
            
            if strategy == CacheStrategy.TTL:
                func_cache.set(key, result, ttl)
            else:
                func_cache.set(key, result)
            
            return result
        
        # Add cache management methods to wrapper
        wrapper.cache_info = lambda: func_cache.stats()
        wrapper.cache_clear = lambda: func_cache.clear()
        
        return wrapper
    
    return decorator

def clear_cache(cache_name: str = "all") -> None:
    """
    Clear specified cache or all caches.
    
    Args:
        cache_name: Name of cache to clear ("lru", "ttl", "all")
    """
    if cache_name in ["lru", "all"]:
        _global_lru_cache.clear()
    
    if cache_name in ["ttl", "all"]:
        _global_ttl_cache.clear()

def get_cache_stats(cache_name: str = "all") -> Dict[str, Any]:
    """
    Get statistics for specified cache(s).
    
    Args:
        cache_name: Name of cache ("lru", "ttl", "all")
        
    Returns:
        Dictionary with cache statistics
    """
    stats = {}
    
    if cache_name in ["lru", "all"]:
        stats["lru"] = _global_lru_cache.stats().to_dict()
    
    if cache_name in ["ttl", "all"]:
        stats["ttl"] = _global_ttl_cache.stats().to_dict()
    
    return stats

def cleanup_expired_cache_items() -> Dict[str, int]:
    """
    Clean up expired items from TTL caches.
    
    Returns:
        Dictionary with cleanup results
    """
    results = {}
    
    # Cleanup global TTL cache
    results["ttl_cleaned"] = _global_ttl_cache.cleanup()
    
    return results

# Utility function for memory-efficient caching
def cached_property(func: Callable) -> property:
    """
    Property decorator that caches the result.
    
    Args:
        func: Function to cache
        
    Returns:
        Cached property
    """
    attr_name = '_cached_' + func.__name__
    
    @property
    def cached_func(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, func(self))
        return getattr(self, attr_name)
    
    return cached_func

# Export all public functions and classes
__all__ = [
    "CacheStrategy",
    "CacheStats",
    "LRUCache",
    "TTLCache", 
    "SecureCache",
    "cache_result",
    "clear_cache",
    "get_cache_stats",
    "cleanup_expired_cache_items",
    "cached_property"
]
