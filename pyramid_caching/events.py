from zope.interface import implementer

from pyramid_caching.interfaces import ICacheHit, ICacheMiss


@implementer(ICacheHit)
class CacheHit(object):
    """An instance of this class is emitted as an event when the cache manager
    could successfully retrieve an object from the cache.
    """
    def __init__(self, key_prefix, request=None):
        self.key_prefix = key_prefix
        self.request = request


@implementer(ICacheMiss)
class CacheMiss(object):
    """An instance of this class is emitted as an event when the cache manager
    could not return an item from the cache and the object instance was created
    by querying the application.
    """
    def __init__(self, key_prefix, request=None):
        self.key_prefix = key_prefix
        self.request = request
