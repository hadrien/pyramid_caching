import unittest


class ViewCacheHitEventTests(unittest.TestCase):
    def test_class_implements_interface(self):
        from pyramid_caching.events import ViewCacheHit
        from pyramid_caching.interfaces import ICacheHit
        from zope.interface.verify import verifyClass
        verifyClass(ICacheHit, ViewCacheHit)

    def test_instance_implements_interface(self):
        from pyramid_caching.events import ViewCacheHit
        from pyramid_caching.interfaces import ICacheHit
        from zope.interface.verify import verifyObject
        request = DummyRequest()
        event = ViewCacheHit(None, request)
        verifyObject(ICacheHit, event)

    def test_attributes(self):
        from pyramid_caching.events import ViewCacheHit
        key = object()
        request = DummyRequest()
        event = ViewCacheHit(key, request)
        self.assertEqual(event.request, request)
        self.assertEqual(event.cache_key, key)


class ViewCacheMissEventTests(unittest.TestCase):
    def test_class_implements_interface(self):
        from pyramid_caching.events import ViewCacheMiss
        from pyramid_caching.interfaces import ICacheMiss
        from zope.interface.verify import verifyClass
        verifyClass(ICacheMiss, ViewCacheMiss)

    def test_instance_implements_interface(self):
        from pyramid_caching.events import ViewCacheMiss
        from pyramid_caching.interfaces import ICacheMiss
        from zope.interface.verify import verifyObject
        request = DummyRequest()
        event = ViewCacheMiss("a_key", request)
        verifyObject(ICacheMiss, event)

    def test_attributes(self):
        from pyramid_caching.events import ViewCacheMiss
        key = object()
        request = DummyRequest()
        event = ViewCacheMiss(key, request)
        self.assertEqual(event.request, request)
        self.assertEqual(event.cache_key, key)


class DummyRequest:
    pass
