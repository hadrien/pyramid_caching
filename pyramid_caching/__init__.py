import os
from pyramid.settings import asbool


def includeme(config):
    """Pyramid_caching main includeme.

    The extension is enabled by default. You can disable all mechanisms with:

    - environment variable CACHING_ENABLED=false
    - setting caching.enabled = false
    """
    parse_settings(config)

    if config.registry.settings['caching.enabled']:
        config.include('.versioner')
        config.include('.key_versioner')
        config.include('.serializers')
        config.include('.cache')


def parse_settings(config):
    cache_enabled = config.registry.settings.get('caching.enabled', 'true')
    cache_enabled = os.getenv('CACHING_ENABLED', cache_enabled)
    config.registry.settings['caching.enabled'] = asbool(cache_enabled)
