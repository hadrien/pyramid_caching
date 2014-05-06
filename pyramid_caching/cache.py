import inspect

import venusian
from zope.interface import implementer

from pyramid_caching.interfaces import ICacheClient


def includeme(config):
    config.add_directive('add_basic_cache', add_basic_cache)
    config.add_directive('get_cache_client', get_cache_client,
                         action_wrap=False)

    cache_client = MemoryCacheClient()
    config.registry.registerUtility(cache_client)

    config.add_request_method(get_cache_client, 'cache_client', reify=True)
    config.scan(__name__)


@implementer(ICacheClient)
class MemoryCacheClient(object):

    def __init__(self):
        self.cache = dict()

    def get(self, key):
        return self.cache.get(key)

    def set(self, key, value):
        self.cache[key] = value


def get_cache_client(config_or_request):
    return config_or_request.registry.getUtility(ICacheClient)


def add_basic_cache(config, name, wrapped, attach_info):
    versioner = config.get_versioner()
    cache_client = config.get_cache_client()

    module = attach_info.module

    args_spec = inspect.getargspec(wrapped)

    def cached_func(*args, **kwargs):
        identities = ['%s=%s' % (varname, value)
                      for (varname, value) in zip(args_spec.args, args)]
        versionned_keys = versioner.get_multi_keys(identities)

        cache_key = '%s:%s' % (name, ':'.join(versionned_keys))

        result = cache_client.get(cache_key)
        if not result:
            result = wrapped(*args, **kwargs)

            cache_client.set(cache_key, result)

        return result

    setattr(module, name, cached_func)


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
        versioner = request.versioner
        cache_client = request.cache_client

        models = []
        for cls, options in self.depends_on.iteritems():

            ids_dict = {}
            if 'matchdict' in options:
                for match in options['matchdict']:
                    ids_dict.update({match: request.matchdict[match]})

            models.append((cls, ids_dict))

        versionned_keys = versioner.get_multi_keys(models)
        # XXX: add content_type in cache_key
        cache_key = '%s:%s:%s' % (
            self.view.__module__,
            self.view.__name__,
            ':'.join(versionned_keys)
            )
        result = cache_client.get(cache_key)

        if result is None:
            result = self.view(context, request)

            cache_client.set(cache_key, result)

        return result
