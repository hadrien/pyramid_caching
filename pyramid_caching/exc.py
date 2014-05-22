

class Base(Exception):
    """Base exception for pyramid_caching"""

class CacheError(Base):
    """Base exception for cache client"""

class CacheKeyAlreadyExists(CacheError):
    """Trying to create an existing key in cache"""

class CacheAddFailure(CacheError):
    """Failure on cache key creation"""

class CacheGetFailure(CacheError):
    """Failure on cache key retrieval"""


class VersionError(Base):
    """Base exception for version client"""

class VersionGetFailure(VersionError):
    """Failure on model version increment operation"""

class VersionIncrementFailure(VersionError):
    """Failure on model version increment operation"""

class VersionMasterVersionFailure(VersionError):
    """Failure on master version operation"""
