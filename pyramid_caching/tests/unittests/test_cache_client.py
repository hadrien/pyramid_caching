import unittest

import mock
from nose_parameterized import parameterized

from pyramid_caching.ext.redis import RedisCacheWrapper
from pyramid_caching.exc import (
    CacheKeyAlreadyExists,
    CacheAddError,
    CacheGetError,
    )

from redis import RedisError


class MockClient(object):
    def __init__(self, m_set, m_get, m_flush):
        self.m_set = m_set
        self.m_get = m_get
        self.m_flush = m_flush

    def set(self, *args, **kwargs):
        return self.m_set(*args, **kwargs)

    def get(self, *args, **kwargs):
        return self.m_get(*args, **kwargs)

    def flushall(self, *args, **kwargs):
        return self.m_flush(*args, **kwargs)


def get_redis(**kwargs):
    m_set = mock.Mock(name='add')
    m_get = mock.Mock(name='get')
    m_flush = mock.Mock(name='get')
    m_client = MockClient(m_set=m_set, m_get=m_get, m_flush=m_flush)
    return (m_set, m_get, m_flush, RedisCacheWrapper(m_client))

CACHE_CLIENTS = [
    ("redis", get_redis, '0'),
]


class TestCacheClient(unittest.TestCase):

    def setUp(self):
        m_set, m_get, m_flush, cache = get_redis()
        cache.flush_all()

    @parameterized.expand(CACHE_CLIENTS)
    def test_interface(self, name, get_cache, default_value):
        from zope.interface.verify import verifyObject
        from pyramid_caching.interfaces import ICacheClient

        m_set, m_get, m_flush, cache = get_cache()

        self.assertTrue(verifyObject(ICacheClient, cache))

    @parameterized.expand(CACHE_CLIENTS)
    def test_flush_all(self, name, get_cache, default_value):
        """Note: we use flush_all() for testing, so let's validate it first"""
        m_set, m_get, m_flush, cache = get_cache()

        cache.flush_all()
        m_flush.assert_called_once()

    @parameterized.expand(CACHE_CLIENTS)
    def test_add_ok(self, name, get_cache, default_value):
        m_set, m_get, m_flush, cache = get_cache()

        ex = 3600 * 24 * 7
        cache.add('FOO', 'BAR', expiration=ex)
        m_set.assert_called_once_with('FOO', 'BAR', ex=ex, nx=True)

    @parameterized.expand(CACHE_CLIENTS)
    def test_add_with_expiration(self, name, get_cache, default_value):
        m_set, m_get, m_flush, cache = get_cache()

        ex = 42
        cache.add('FOO', 'BAR', expiration=ex)
        m_set.assert_called_once_with('FOO', 'BAR', ex=ex, nx=True)

    @parameterized.expand(CACHE_CLIENTS)
    def test_add_exists(self, name, get_cache, default_value):
        m_set, m_get, m_flush, cache = get_cache()

        m_set.return_value = None
        with self.assertRaises(CacheKeyAlreadyExists):
            cache.add('FOO', 'BAR')

    @parameterized.expand(CACHE_CLIENTS)
    def test_add_network_error(self, name, get_cache, default_value):
        m_set, m_get, m_flush, cache = get_cache()

        m_set.side_effect = RedisError()
        with self.assertRaises(CacheAddError):
            cache.add('FOO', 'BAR')

    @parameterized.expand(CACHE_CLIENTS)
    def test_get_ok(self, name, get_cache, default_value):
        m_set, m_get, m_flush, cache = get_cache()

        m_get.return_value = 'BAR'
        self.assertEquals(cache.get('FOO'), 'BAR')

    @parameterized.expand(CACHE_CLIENTS)
    def test_get_network_error(self, name, get_cache, default_value):
        m_set, m_get, m_flush, cache = get_cache()

        m_get.side_effect = RedisError()

        with self.assertRaises(CacheGetError):
            cache.get('FOO')
