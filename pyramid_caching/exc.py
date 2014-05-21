
class CacheError(Exception):
    """Base exception for cache client"""

class CacheKeyAlreadyExists(CacheError):
    pass
