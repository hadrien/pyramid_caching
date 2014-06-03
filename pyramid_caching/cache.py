from collections import namedtuple
import hashlib
import logging

from zope.interface import implementer, classImplements

from pyramid_caching.events import ViewCacheHit, ViewCacheMiss
from pyramid_caching.interfaces import (
    ICacheClient,
    ICacheManager,
    )
from pyramid_caching.exc import (
    CacheDisabled,
    )

log = logging.getLogger(__name__)


def includeme(config):
    """Set up a request method to access the cache manager utility."""
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
        key = CacheKey(prefixes, versioned_keys)

        cache_content = self.cache_client.get(str(key))

        if cache_content is not None:
            result = self.serializer.loads(cache_content)
            return CacheResult.hit(key, result)
        else:
            result = get_result()
            data = self.serializer.dumps(result)
            self.cache_client.add(str(key), data)
            return CacheResult.miss(key, result)


class CacheKey(object):

    """A key identifying a version of a complex resource in a cache.

    This object specifies the formatting of cache keys from a list of base
    resource names (for example, a unique way to identify a Pyramid view
    callable) and a list of names that define the current context of the view
    (for example, a list of model names and the primary keys matching the
    route).

    ::
       key = CacheKey(['mypackage.views', 'hello_view'], ['user:bob'])
       key.root() --> 'mypackage.views:hello_view'
       str(key) --> 'mypackage.views:hello_view:user:bob'

    """

    def __init__(self, bases, dependencies):
        self.bases = bases
        self.dependencies = dependencies

    def root(self):
        """The static part that refers to a single view or model class."""
        return ':'.join(self.bases)

    def key(self):
        """The unique cache key identifying a resource and its context."""
        return self.root() + ':' + ':'.join(self.dependencies)

    def __str__(self):
        return self.key()


_CacheResultInfo = namedtuple("CacheResultInfo", ["key", "hit"])


class CacheResult(object):

    """A versioned cache response based on a unique key."""

    def __init__(self, cache_key, data, hit):
        self._cache_key = cache_key
        self.data = data
        self._hit = hit

    @classmethod
    def hit(cls, cache_key, data):
        """Specify that this data was fetched from the cache."""
        return cls(cache_key, data, True)

    @classmethod
    def miss(cls, cache_key, data):
        """Specify that this data was loaded from the application."""
        return cls(cache_key, data, False)

    def key_hash(self):
        """Unique hash to identify this result in the cache.

        A string corresponding to a cryptographic hash digest of the cache key
        that uniquely defines the version of this result.
        """
        m = hashlib.sha1()
        m.update(str(self._cache_key))
        return m.hexdigest()

    def info(self):
        return _CacheResultInfo(self._cache_key, self._hit)


class cache_factory(object):

    """Decorator that defines the model dependencies for a view method.

    ::
       @cache_factory(depends_on={User: {'matchdict': 'user'}})
       def hello_view(context, request):
           user = User(request.matchdict['user'])
           return "Hello, {}".format(user.name)

    """

    def __init__(self, depends_on=None):
        self.depends_on = depends_on

    def __call__(self, view):
        return ViewCacheDecorator(view, self.depends_on)


class ViewCacheDecorator(object):

    def __init__(self, view, depends_on=None):
        self.view = view
        self.depends_on = depends_on

    def __call__(self, context, request):
        def get_result():
            return self.view(context, request)

        def nocache_result():
            response = get_result()
            response.headers['X-View-Cache'] = 'DISABLED'
            return response

        if not request.registry.settings['caching.enabled']:
            return nocache_result()

        cache_manager = request.cache_manager

        prefixes = [self.view.__module__, self.view.__name__]
        dependencies = self.get_dependencies(request.matchdict)

        try:
            result = cache_manager.get_or_cache(get_result,
                                                prefixes,
                                                dependencies)
        except CacheDisabled:
            return nocache_result()

        response = result.data
        result_info = result.info()
        if result_info.hit:
            request.registry.notify(ViewCacheHit(result_info.key, request))
            response.headers['X-View-Cache'] = 'HIT'
        else:
            request.registry.notify(ViewCacheMiss(result_info.key, request))
            response.headers['X-View-Cache'] = 'MISS'
        response.headers['ETag'] = result.key_hash()
        return response

    def get_dependencies(self, matchdict):
        dependencies = []
        for cls, options in self.depends_on.iteritems():

            ids_dict = {}
            if 'matchdict' in options:
                for match in options['matchdict']:
                    ids_dict.update({match: matchdict[match]})

            dependencies.append((cls, ids_dict))
        return dependencies
