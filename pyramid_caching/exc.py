class Base(Exception):
    """Base exception for pyramid_caching"""


class CacheError(Base):
    """Base exception for cache client"""


class CacheKeyAlreadyExists(CacheError):
    """Trying to create an existing key in cache"""


class SerializationError(Exception):
    """An error that occurs if no encoder can be found matching the object
    type to serialize."""


class DeserializationError(Exception):
    """An error that occurs when valid cached data could not be decoded."""
