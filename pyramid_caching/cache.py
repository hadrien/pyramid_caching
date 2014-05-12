import inspect

import venusian
from zope.interface import implementer

from pyramid_caching.interfaces import ICacheClient, ICacheManager


def includeme(config):
    cache_client = MemoryCacheClient()
    config.registry.registerUtility(cache_client)

    manager = Manager(config.get_versioner(), cache_client)
    config.registry.registerUtility(manager)

    config.add_directive('add_basic_cache', add_basic_cache)
    config.add_directive('get_cache_client', get_cache_client,
                         action_wrap=False)
    config.add_directive('get_cache_manager', get_cache_manager,
                         action_wrap=False)
    config.add_request_method(get_cache_manager, 'cache_manager', reify=True)
    config.scan(__name__)


def get_cache_client(config_or_request):
    return config_or_request.registry.getUtility(ICacheClient)


def get_cache_manager(config_or_request):
    return config_or_request.registry.getUtility(ICacheManager)


def add_basic_cache(config, name, wrapped, attach_info):
    manager = config.get_cache_manager()
    manager.add_basic_cache(config, name, wrapped, attach_info)


@implementer(ICacheManager)
class Manager(object):

    def __init__(self, versioner, cache_client):
        self.versioner = versioner
        self.cache_client = cache_client

    def add_basic_cache(self, config, name, wrapped, attach_info):
        module = attach_info.module

        args_spec = inspect.getargspec(wrapped)

        def cached_func(*args, **kwargs):

            def get_result():
                return wrapped(*args, **kwargs)

            prefixes = [wrapped.__module__, wrapped.__name__]
            dependencies = [{k: v} for k, v in zip(args_spec.args, args)]

            return self.get_or_cache(get_result, prefixes, dependencies)

        def undecorate_me(event):
            setattr(module, name, wrapped)

        config.add_subscriber(undecorate_me, UndecorateEvent)

        setattr(module, name, cached_func)

    def get_or_cache(self, get_result, prefixes, dependencies):
        versioned_keys = self.versioner.get_multi_keys(dependencies)

        cache_key = ':'.join(prefixes + versioned_keys)

        result = self.cache_client.get(cache_key)
        if result is None:
            result = get_result()

            self.cache_client.set(cache_key, result)

        return result


class UndecorateEvent(object):
    pass


class cache_basic(object):

    def __call__(self, wrapped):

        def callback(context, name, wrapped):
            config = context.config.with_package(info.module)
            config.add_basic_cache(name, wrapped, info, **settings)

        info = venusian.attach(wrapped, callback)
        settings = {'_info': info.codeinfo}
        return wrapped


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

        accept_header = str(request.accept)
        if accept_header:
            prefixes.append(accept_header)

        return cache_manager.get_or_cache(get_result, prefixes, dependencies)


@implementer(ICacheClient)
class MemoryCacheClient(object):

    def __init__(self):
        self.cache = dict()

    def get(self, key):
        return self.cache.get(key)

    def set(self, key, value):
        self.cache[key] = value
