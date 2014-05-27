import unittest


class CacheHitEventTests(unittest.TestCase):
    def test_class_implements_interface(self):
        from pyramid_caching.events import CacheHit
        from pyramid_caching.interfaces import ICacheHit
        from zope.interface.verify import verifyClass
        verifyClass(ICacheHit, CacheHit)

    def test_instance_implements_interface(self):
        from pyramid_caching.events import CacheHit
        from pyramid_caching.interfaces import ICacheHit
        from zope.interface.verify import verifyObject
        request = DummyRequest()
        event = CacheHit("a_key", request=request)
        verifyObject(ICacheHit, event)

    def test_attributes(self):
        from pyramid_caching.events import CacheHit
        request = DummyRequest()
        event = CacheHit("a_key", request=request)
        self.assertEqual(event.request, request)
        self.assertEqual(event.key_prefix, "a_key")


class CacheMissEventTests(unittest.TestCase):
    def test_class_implements_interface(self):
        from pyramid_caching.events import CacheMiss
        from pyramid_caching.interfaces import ICacheMiss
        from zope.interface.verify import verifyClass
        verifyClass(ICacheMiss, CacheMiss)

    def test_instance_implements_interface(self):
        from pyramid_caching.events import CacheMiss
        from pyramid_caching.interfaces import ICacheMiss
        from zope.interface.verify import verifyObject
        request = DummyRequest()
        event = CacheMiss("a_key", request=request)
        verifyObject(ICacheMiss, event)

    def test_attributes(self):
        from pyramid_caching.events import CacheMiss
        request = DummyRequest()
        event = CacheMiss("a_key", request=request)
        self.assertEqual(event.request, request)
        self.assertEqual(event.key_prefix, "a_key")


class DummyRequest:
    pass
