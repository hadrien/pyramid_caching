
class Base(Exception):
    """Base exception for pyramid_caching"""


class CacheError(Base):
    """Base exception for cache client"""


class CacheKeyAlreadyExists(CacheError):
    """Trying to create an existing key in cache"""


class CacheAddError(CacheError):
    """Error on cache key creation"""


class CacheGetError(CacheError):
    """Error on cache key retrieval"""


class VersionError(Base):
    """Base exception for version client"""


class VersionGetError(VersionError):
    """Error on model version increment operation"""


class VersionIncrementError(VersionError):
    """Error on model version increment operation"""


class VersionMasterVersionError(VersionError):
    """Error on master version operation"""


class VersionInhibitCaching(VersionError):
    """Version Store inhibit caching"""


class SerializationError(Exception):
    """An error that occurs if no encoder can be found matching the object
    type to serialize."""


class DeserializationError(Exception):
    """An error that occurs when valid cached data could not be decoded."""
