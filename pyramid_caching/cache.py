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

    def _flatten(self, item):
        if isinstance(item, dict):
            return ':'.join(["%s=%s" % (k, v)
                             for k, v in sorted(item.iteritems())])
        elif isinstance(item, list):
            return ':'.join([self._flatten(x) for x in item])
        return item

    def root(self):
        """The static part that refers to a single view or model class."""
        return self._flatten(self.bases)

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
       @view_config(
           decorator=cache_factory(
               predicates=[
                   QueryStringPredicate(['name']),
                   ],
               depends_on=[
                   RouteDependency(User, {'user_id': 'id'}),
                   ],
               )
       def hello_view(context, request):
           user = User(request.matchdict['user'])
           return "Hello, {}".format(user.name)

    """

    def __init__(self, predicates=None, depends_on=None):
        self.predicates = predicates
        self.depends_on = depends_on

    def __call__(self, view):
        return ViewCacheDecorator(view,
                                  predicates=self.predicates,
                                  depends_on=self.depends_on,
                                  )


class ViewCacheDecorator(object):

    def __init__(self, view, predicates=None, depends_on=None):
        self.view = view
        self.predicates = predicates or []
        self.depends_on = depends_on or []

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
        prefixes.extend(self.get_predicates(request))

        dependencies = self.get_dependencies(request)

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

    def get_predicates(self, request):
        return [pred(request) for pred in self.predicates]

    def get_dependencies(self, request):
        return [dep(request) for dep in self.depends_on]


class CollectionDependency(object):

    """Model dependency on the collection of all items."""

    def __init__(self, model_class):
        self.model_class = model_class

    def __call__(self, request):
        return self.model_class


class RouteDependency(object):

    """Model dependency on route segment.

    Use to specify the relationships between the matched route segment elements
    and the column names of the model primary keys.

    For example, for a view where the route pattern `r'/users/{user_id}'`,
    and the `user_id` element is related to the `id` column of the `User`
    model, the dependency can be written as:

    ::
       @view_config(
           decorator=cache_factory(depends_on=[
               RouteDependency(User, {'user_id': 'id'}),
               ])
       def user_view(context, request):
           pass

    When a request in received, the model instance identity will be generated
    by matched route segment elements (the matchdict items). For a request for
    `/users/sue`, it would generate:

    ::
       identity_from_request(request) --> {'id': 'sue'}
    """

    def __init__(self, model_class, primary_key_elements):
        self.model_class = model_class
        self.primary_key_elements = primary_key_elements

    def __call__(self, request):
        return (self.model_class,
                dict((pk, request.matchdict[element])
                     for element, pk in self.primary_key_elements.iteritems())
                )


class QueryStringPredicate(object):

    """Cached resource predicate based on query string parameters."""

    def __init__(self, params):
        self.params = params

    def __call__(self, request):
        return dict((p, request.params[p])
                    for p in self.params
                    if p in request.params)
