import unittest

from pyramid import testing


class CacheManagerTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.registry = self.config.registry

    def tearDown(self):
        testing.tearDown()

    def _make_one(self, hit=None):
        from pyramid_caching.cache import Manager
        return Manager(self.registry,
                       DummyVersioner(),
                       DummyClient(hit),
                       DummySerializer())

    def _register_event_listener(self, iface):
        events = []

        def listener(event):
            events.append(event)

        self.registry.registerHandler(listener, (iface,))
        return events

    def test_cache_hit_event(self):
        from pyramid_caching.interfaces import ICacheHit
        hit_events = self._register_event_listener(ICacheHit)

        def get_result():
            pass

        manager = self._make_one(hit=True)
        manager.get_or_cache(get_result, ['a', 'b'], [])

        self.assertEqual(len(hit_events), 1)

    def test_cache_miss_event(self):
        from pyramid_caching.interfaces import ICacheMiss
        miss_events = self._register_event_listener(ICacheMiss)

        def get_result():
            pass

        manager = self._make_one(hit=False)
        manager.get_or_cache(get_result, ['a', 'b'], [])

        self.assertEqual(len(miss_events), 1)


class DummyVersioner:
    def get_multi_keys(self, dependencies):
        return ['c', 'd']


class DummyClient:
    def __init__(self, hit):
        self.hit = hit

    def get(self, key):
        if self.hit:
            return key
        else:
            return None

    def add(self, key, value):
        pass


class DummySerializer:
    def loads(self, data):
        return data

    def dumps(self, data):
        return data
