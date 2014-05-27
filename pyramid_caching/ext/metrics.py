"""An extension that records the performance of the caching layer by sending
information about cache hits and cache misses events to a statistics aggregator
via pyramid_metrics.
"""

from pyramid.events import subscriber

from pyramid_caching.events import CacheHit, CacheMiss


def includeme(config):
    """Include subscriptions to cache hit and cache miss events into the
    specified Pyramid configurator. This will allow the application to
    automatically provide cache performance statistics.

    To activate this extension, call the configurator method:

    .. code-block:: python

       config.include('pyramid_caching.ext.metrics')

    """
    config.include('pyramid_metrics')
    config.scan()


@subscriber(CacheHit)
def cache_hit(event):
    if event.request is not None:
        event.request.metrics.incr(('cache.hit', event.key_prefix))


@subscriber(CacheMiss)
def cache_miss(event):
    if event.request is not None:
        event.request.metrics.incr(('cache.miss', event.key_prefix))
