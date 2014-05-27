import logging

log = logging.getLogger(__name__)


def includeme(config):  # pragma no cover
    config.include('pyramid_caching')
    try:
        config.include('pyramid_caching.ext.metrics')
    except ImportError:
        log.warning('Cache performance metrics library not available.')
    config.include('pyramid_caching.ext.redis')
    config.include('.model')
    config.include('.views')
