import unittest

from pyramid import testing
from pyramid.response import Response

from pyramid_caching.cache import CacheResult


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

    def _make_one(self, predicates=None, depends_on=None, hit=True):
        from pyramid_caching.cache import ViewCacheDecorator
        request = testing.DummyRequest()
        request.registry.settings['caching.enabled'] = True
        request.cache_manager = DummyCacheManager(hit)
        return request, ViewCacheDecorator(self._view,
                                           predicates=predicates,
                                           depends_on=depends_on)

    def test_key_base_from_view_name(self):
        request, deco = self._make_one()
        deco(None, request)
        self.assertEqual(request.cache_manager.prefixes, [__name__, '_view'])

    def test_key_dependencies_from_route(self):
        from pyramid_caching.cache import RouteDependency
        request, deco = self._make_one(depends_on=[
            RouteDependency('User', {'user_id': 'id'}),
            ])
        request.matchdict = {'user_id': '123'}
        deco(None, request)
        self.assertEqual(request.cache_manager.dependencies,
                         [('User', {'id': '123'})])

    def test_key_prefix_from_query_string(self):
        from pyramid_caching.cache import QueryStringPredicate
        request, deco = self._make_one(predicates=[
            QueryStringPredicate(['name']),
            ])
        request.params = {'name': 'bob', 'utm_campaign': 'xxxx'}
        deco(None, request)
        self.assertEqual(request.cache_manager.prefixes[-1],
                         {'name': 'bob'})

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
    def __init__(self, hit=True):
        self.hit = hit

    def get_or_cache(self, get_result, prefixes, dependencies):
        self.get_result = get_result
        self.prefixes = prefixes
        self.dependencies = dependencies
        if self.hit:
            return CacheResult.hit('key', Response())
        else:
            return CacheResult.miss('key', Response())
