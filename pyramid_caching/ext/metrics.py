"""An extension that records the performance of the caching layer by sending
information about cache hits and cache misses events to a statistics aggregator
via pyramid_metrics.
"""

from pyramid.events import subscriber
from pyramid_metrics.utility import get_current_metrics

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
    count_cache_event(event, 'hit')


@subscriber(CacheMiss)
def cache_miss(event):
    count_cache_event(event, 'miss')


def count_cache_event(event, access):
    if event.request is not None:
        metrics = event.request.metrics
    else:
        metrics = get_current_metrics()
    if metrics is not None:
        metrics.incr(('cache.%s' % access, event.key_prefix))
