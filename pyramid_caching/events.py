from zope.interface import implementer

from pyramid_caching.interfaces import ICacheHit, ICacheMiss


@implementer(ICacheHit)
class ViewCacheHit(object):
    """An instance of this class is emitted as an event when the cache manager
    could successfully retrieve a Response object from the cache.
    """
    def __init__(self, cache_key, request):
        self.cache_key = cache_key
        self.request = request


@implementer(ICacheMiss)
class ViewCacheMiss(object):
    """An instance of this class is emitted as an event when the cache manager
    could not retrieve the response from the cache and the object instance was
    created by calling the view method.
    """
    def __init__(self, cache_key, request):
        self.cache_key = cache_key
        self.request = request
