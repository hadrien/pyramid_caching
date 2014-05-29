import unittest

from pyramid_caching.cache import CacheKey


class TestMetricsExtension(unittest.TestCase):
    def test_cache_hit(self):
        from pyramid_caching.ext.metrics import cache_hit
        event = DummyEvent()
        cache_hit(event)
        self.assertEqual(len(event.request.metrics.keys), 1)
        self.assertEqual(event.request.metrics.keys[0], ('cache.hit', 'a:b'))

    def test_cache_miss(self):
        from pyramid_caching.ext.metrics import cache_miss
        event = DummyEvent()
        cache_miss(event)
        self.assertEqual(len(event.request.metrics.keys), 1)
        self.assertEqual(event.request.metrics.keys[0], ('cache.miss', 'a:b'))


class DummyEvent:
    def __init__(self):
        self.request = DummyRequest()
        self.cache_key = CacheKey(['a', 'b'], [])


class DummyRequest:
    def __init__(self):
        self.metrics = DummyMetrics()


class DummyMetrics:
    def __init__(self):
        self.keys = []

    def incr(self, key):
        self.keys.append(key)
