"""An extension that records the performance of the caching layer by sending
information about cache hits and cache misses events to a statistics aggregator
via pyramid_metrics.
"""

from pyramid.events import subscriber

from pyramid_caching.events import ViewCacheHit, ViewCacheMiss


def includeme(config):
    """Include subscriptions to cache hit and cache miss events into the
    specified Pyramid configurator. This will allow the application to
    automatically provide cache performance statistics.

    To activate this extension, call the configurator method:

    .. code-block:: python

       config.include('pyramid_caching.ext.metrics')

    """
    config.include('pyramid_metrics')
    config.scan(__name__)


@subscriber(ViewCacheHit)
def cache_hit(event):
    count_view_cache_event(event, 'hit')


@subscriber(ViewCacheMiss)
def cache_miss(event):
    count_view_cache_event(event, 'miss')


def count_view_cache_event(event, access):
    metrics = event.request.metrics
    metrics.incr(('cache.%s' % access, event.cache_key.root()))
