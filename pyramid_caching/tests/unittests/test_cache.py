import unittest

from pyramid import testing
from pyramid.response import Response
from webob.multidict import MultiDict

from pyramid_caching.cache import CacheResult
from pyramid_caching.exc import CacheGetError, VersionGetError


class CacheManagerTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.registry = self.config.registry

    def tearDown(self):
        testing.tearDown()

    def _make_one(self, cached_value):
        from pyramid_caching.cache import Manager
        return Manager(self.registry,
                       DummyVersioner(),
                       DummyClient(cached_value),
                       DummySerializer())

    def test_key_root_from_bases(self):
        manager = self._make_one(True)
        result = manager.get_or_cache(None, ['a', 'b'], [])
        self.assertEqual(result._cache_key.root(), 'a:b')

    def test_key_from_dependencies(self):
        manager = self._make_one(True)
        result = manager.get_or_cache(None, ['a', 'b'], ['c', 'd'])
        self.assertEqual(result._cache_key.key(), 'a:b:c:d')

    def test_cache_miss_when_client_returns_none(self):
        def get_result():
            pass

        manager = self._make_one(None)
        result = manager.get_or_cache(get_result, [], [])
        self.assertFalse(result.info().hit)

    def test_cache_hit_when_client_returns_object(self):
        def get_result():
            pass

        manager = self._make_one(object())
        result = manager.get_or_cache(get_result, ['a', 'b'], ['c', 'd'])
        self.assertTrue(result.info().hit)

    def test_cache_miss_loads_data_from_function(self):
        def get_result():
            return "loaded"

        manager = self._make_one(None)
        result = manager.get_or_cache(get_result, [], [])
        self.assertEqual(result.data, "loaded")


class ViewCacheDecoratorTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp(settings={
            'caching.enabled': False,
            })

    def tearDown(self):
        testing.tearDown()

    def _view(self, context, request):
        return Response('ok')

    def test_decorates_method(self):
        from pyramid_caching.cache import cache_factory

        @cache_factory()
        def view(context, request):
            return Response('ok')

        request = testing.DummyRequest()
        response = view(None, request)
        self.assertEqual(response.body, "ok")

    def _make_one(self, varies_on=None, depends_on=None, hit=True, fail_with=None):
        from pyramid_caching.cache import ViewCacheDecorator
        request = testing.DummyRequest()
        request.registry.settings['caching.enabled'] = True
        request.scheme = 'https'
        request.cache_manager = DummyCacheManager(hit=hit, fail_with=fail_with)
        return request, ViewCacheDecorator(self._view,
                                           varies_on=varies_on,
                                           depends_on=depends_on)

    def test_key_base_from_view_name(self):
        request, deco = self._make_one()
        deco(None, request)
        self.assertEqual(request.cache_manager.prefixes,
                         [__name__, '_view', 'https'])

    def test_key_dependencies_from_route(self):
        from pyramid_caching.cache import RouteDependency
        request, deco = self._make_one(depends_on=[
            RouteDependency('User', {'user_id': 'id'}),
            ])
        request.matchdict = {'user_id': '123'}
        deco(None, request)
        self.assertEqual(request.cache_manager.dependencies,
                         [('User', {'id': '123'})])

    def test_key_dependencies_from_resource(self):
        from pyramid_caching.cache import ResourceDependency
        users = testing.DummyResource(__name__='users', __composite__=True)
        item = testing.DummyResource(__name__='alice', __parent__=users)
        request, deco = self._make_one(depends_on=[
            ResourceDependency(),
            ])
        context = item
        deco(context, request)
        self.assertEqual(request.cache_manager.dependencies,
                         [({'users': 'alice'},)])

    def test_key_dependencies_from_composite_resource(self):
        from pyramid_caching.cache import ResourceDependency
        root = testing.DummyResource()
        users = testing.DummyResource(__name__='users',
                                      __parent__=root,
                                      __composite__=True)
        request, deco = self._make_one(depends_on=[
            ResourceDependency(),
            ])
        context = users
        deco(context, request)
        self.assertEqual(request.cache_manager.dependencies,
                         [('users',)])

    def test_key_dependencies_from_resource_root(self):
        from pyramid_caching.cache import ResourceDependency
        root = testing.DummyResource()
        request, deco = self._make_one(depends_on=[
            ResourceDependency(),
            ])
        context = root
        deco(context, request)
        self.assertEqual(request.cache_manager.dependencies,
                         [('__root__',)])

    def test_key_prefix_from_partial_query_string(self):
        from pyramid_caching.cache import QueryStringKeyModifier
        request, deco = self._make_one(varies_on=[
            QueryStringKeyModifier(['name']),
            ])
        request.params = MultiDict(name='bob', utm_campaign='xxxx')
        deco(None, request)
        self.assertEqual(request.cache_manager.prefixes[-1],
                         {'name': ['bob']})

    def test_key_prefix_from_full_query_string(self):
        from pyramid_caching.cache import QueryStringKeyModifier
        request, deco = self._make_one(varies_on=[
            QueryStringKeyModifier(),
            ])
        request.params = MultiDict(name='fred', limit='20')
        deco(None, request)
        self.assertEqual(request.cache_manager.prefixes[-1],
                         {'limit': ['20'], 'name': ['fred']})

    def test_cache_miss_calls_view(self):
        request, deco = self._make_one()
        deco(None, request)
        self.assertEqual(request.cache_manager.get_result().body, "ok")

    def test_sets_etag_from_result(self):
        request, deco = self._make_one()
        response = deco(None, request)
        key_hash = 'a62f2225bf70bfaccbc7f1ef2a397836717377de'  # SHA1 of 'key'
        self.assertEqual(response.headers['ETag'], key_hash)

    def test_sets_cache_result_header(self):
        request, deco = self._make_one()
        response = deco(None, request)
        self.assertEqual(response.headers['X-View-Cache'], 'HIT')

    def test_cache_disabled_result_header(self):
        from pyramid_caching.cache import ViewCacheDecorator
        request = testing.DummyRequest()
        deco = ViewCacheDecorator(self._view, depends_on=[])
        response = deco(None, request)
        self.assertEqual(response.headers['X-View-Cache'], 'DISABLED')

    def _register_event_listener(self, iface):
        events = []

        def listener(event):
            events.append(event)

        self.config.registry.registerHandler(listener, (iface,))
        return events

    def test_cache_hit_event(self):
        from pyramid_caching.interfaces import ICacheHit

        hit_events = self._register_event_listener(ICacheHit)
        request, deco = self._make_one()
        deco(None, request)

        self.assertEqual(len(hit_events), 1)

    def test_cache_miss_event(self):
        from pyramid_caching.interfaces import ICacheMiss

        miss_events = self._register_event_listener(ICacheMiss)
        request, deco = self._make_one(hit=False)
        deco(None, request)
        self.assertEqual(len(miss_events), 1)

    def test_bypass_cache_on_versioner_error(self):
        request, deco = self._make_one(fail_with=VersionGetError)
        response = deco(None, request)
        self.assertEqual(response.headers['X-View-Cache'], 'DISABLED')

    def test_bypass_cache_on_storage_error(self):
        request, deco = self._make_one(fail_with=CacheGetError)
        response = deco(None, request)
        self.assertEqual(response.headers['X-View-Cache'], 'DISABLED')


class DummyVersioner:
    def get_multi_keys(self, dependencies):
        return dependencies


class DummyClient:
    def __init__(self, cached_value):
        self._cached_value = cached_value

    def get(self, key):
        return self._cached_value

    def add(self, key, value):
        pass


class DummySerializer:
    def loads(self, data):
        return data

    def dumps(self, data):
        return data


class DummyCacheManager:
    def __init__(self, fail_with=None, hit=True):
        self.hit = hit
        self.fail_with = fail_with

    def get_or_cache(self, get_result, prefixes, dependencies):
        if self.fail_with is not None:
            raise self.fail_with
        self.get_result = get_result
        self.prefixes = prefixes
        self.dependencies = dependencies
        if self.hit:
            return CacheResult.hit('key', Response())
        else:
            return CacheResult.miss('key', Response())
