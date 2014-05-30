import logging

from zope.interface import implementer, classImplements

from pyramid_caching.events import CacheHit, CacheMiss
from pyramid_caching.interfaces import (
    ICacheClient,
    ICacheManager,
    )

log = logging.getLogger(__name__)


def includeme(config):

    config.add_directive('get_cache_client', get_cache_client,
                         action_wrap=False)

    config.add_directive('get_cache_manager', get_cache_manager,
                         action_wrap=False)

    config.add_directive('add_cache_client', add_cache_client)

    config.add_request_method(get_cache_manager, 'cache_manager', reify=True)

    def register():
        cache_client = config.get_cache_client()
        versioner = config.get_versioner()
        serializer = config.get_serializer()
        manager = Manager(config.registry, versioner, cache_client, serializer)
        config.registry.registerUtility(manager)
        log.debug('registering cache manager %r', manager)

    config.action((__name__, 'cache_manager'), register, order=2)


def get_cache_client(config_or_request):
    return config_or_request.registry.getUtility(ICacheClient)


def get_cache_manager(config_or_request):
    return config_or_request.registry.getUtility(ICacheManager)


def add_cache_client(config, client):
    if not ICacheClient.implementedBy(client.__class__):
        log.debug('assuming %r implements %r', client.__class__, ICacheClient)
        classImplements(client.__class__, ICacheClient)

    def register():
        log.debug('registering cache client %r', client)
        config.registry.registerUtility(client, ICacheClient)

    config.action((__name__, 'cache_client'), register, order=0)


@implementer(ICacheManager)
class Manager(object):

    def __init__(self, registry, versioner, cache_client, serializer):
        self.versioner = versioner
        self.cache_client = cache_client
        self.serializer = serializer
        self.registry = registry

    def get_or_cache(self, get_result, prefixes, dependencies):
        versioned_keys = self.versioner.get_multi_keys(dependencies)

        key_prefix = ':'.join(prefixes)
        cache_key = key_prefix + ':' + ':'.join(versioned_keys)

        cached_result = self.cache_client.get(cache_key)

        if cached_result is None:
            result = get_result()
            data = self.serializer.dumps(result)
            self.cache_client.add(cache_key, data)
            self.registry.notify(CacheMiss(key_prefix))
        else:
            result = self.serializer.loads(cached_result)
            self.registry.notify(CacheHit(key_prefix))

        return result


class cache_factory(object):

    def __init__(self, depends_on=None):
        self.depends_on = depends_on

    def __call__(self, view):
        return ViewCacheDecorator(view, self.depends_on)


class ViewCacheDecorator(object):

    def __init__(self, view, depends_on=None):
        self.view = view
        self.depends_on = depends_on

    def __call__(self, context, request):
        if not request.registry.settings['caching.enabled']:
            # TODO: possible runtime shortcut here
            return self.view(context, request)

        cache_manager = request.cache_manager

        dependencies = []
        for cls, options in self.depends_on.iteritems():

            ids_dict = {}
            if 'matchdict' in options:
                for match in options['matchdict']:
                    ids_dict.update({match: request.matchdict[match]})

            dependencies.append((cls, ids_dict))

        def get_result():
            return self.view(context, request)

        prefixes = [self.view.__module__, self.view.__name__]

        return cache_manager.get_or_cache(get_result,
                                          prefixes,
                                          dependencies,
                                          )
