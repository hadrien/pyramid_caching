

class Base(Exception):
    """Base exception for pyramid_caching"""

class CacheError(Base):
    """Base exception for cache client"""

class CacheKeyAlreadyExists(CacheError):
    """Trying to create an existing key in cache"""
