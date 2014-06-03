import unittest

import mock
from nose_parameterized import parameterized

from pyramid_caching.ext.redis import RedisVersionWrapper
from pyramid_caching.exc import (
    VersionGetError,
    VersionMasterVersionError,
    VersionIncrementError,
    CacheDisabled,
)

from redis import (StrictRedis, RedisError)


def get_redis():
    return RedisVersionWrapper(StrictRedis())


KEY_VERSIONERS = [
    ("redis", get_redis, '0'),
]


class TestKeyVersioner(unittest.TestCase):

    TEST_VALUE = '4'  # Best creative testing value

    def setUp(self):
        get_redis().flush_all()

    @parameterized.expand(KEY_VERSIONERS)
    def test_interface(self, name, get_key_versioner, default_value):
        from zope.interface.verify import verifyObject
        from pyramid_caching.interfaces import IKeyVersioner

        key_versioner = get_key_versioner()

        self.assertTrue(verifyObject(IKeyVersioner, key_versioner))

    @parameterized.expand(KEY_VERSIONERS)
    @mock.patch('pyramid_caching.ext.redis.time')
    def test_get_multi(self, name, get_key_versioner, default_value, m_time):
        m_time.time.return_value = 1234.123
        key_versioner = get_key_versioner()

        KEYS = ['FOO', 'BAR', '2000']
        VERSIONS = [('cache', '1234'),
                    ('FOO', '0'),
                    ('BAR', '0'),
                    ('2000', '0')]

        self.assertEqual(key_versioner.get_multi(KEYS), VERSIONS)
        self.assertEqual(key_versioner.get_multi(KEYS), VERSIONS)

        for _ in range(int(self.TEST_VALUE)):
            key_versioner.incr('BAR')

        VERSIONS[2] = ('BAR', str(self.TEST_VALUE))

        self.assertEqual(key_versioner.get_multi(KEYS), VERSIONS)
        self.assertEqual(key_versioner.get_multi(KEYS), VERSIONS)

        for _ in range(42):
            key_versioner.incr('2000')

        VERSIONS[3] = ('2000', '42')

        self.assertEqual(key_versioner.get_multi(KEYS), VERSIONS)
        self.assertEqual(key_versioner.get_multi(KEYS), VERSIONS)


class TestRedisVersionClient(unittest.TestCase):
    """Test specifics of Redis client"""

    def setUp(self):
        self.redis_client = mock.Mock(name='RedisClient')
        self.version_store = RedisVersionWrapper(self.redis_client)

    def test_get_master_version(self):
        master_version = self.version_store._get_master_version()

        self.assertEqual(master_version, self.redis_client.get.return_value)
        self.redis_client.get.assert_called_once_with('cache')

    def test_set_master_version(self):
        with mock.patch('pyramid_caching.ext.redis.time') as m_t:
            m_t.time.return_value = 42
            self.version_store._set_master_version()

        self.redis_client.set.assert_called_once_with('cache', 42, nx=True)

    def test_get_multi(self):
        keys = ['one', 'two']
        self.redis_client.mget.return_value = ['42', '1', None]

        result = self.version_store.get_multi(keys)

        self.assertEqual(result, [('cache', '42'), ('one', '1'), ('two', '0')])
        self.redis_client.mget.assert_called_once_with(['cache', 'one', 'two'])

    def test_get_multi_no_master_version(self):
        keys = ['one', 'two']
        self.redis_client.mget.return_value = [None, '1', '2']
        self.redis_client.get.return_value = '84'

        with mock.patch('pyramid_caching.ext.redis.time') as m_t:
            m_t.time.return_value = 42
            result = self.version_store.get_multi(keys)

        expected = [('cache', '84'),
                    ('one', '1'),
                    ('two', '2')]
        self.assertEqual(result, expected)
        self.redis_client.set.assert_called_once_with('cache', 42, nx=True)

    def test_get_multi_no_master_version_after_reset_attempt(self):
        keys = []
        self.redis_client.mget.return_value = [None]
        self.redis_client.get.return_value = None

        with mock.patch('pyramid_caching.ext.redis.time') as m_t:
            m_t.time.return_value = 42
            with self.assertRaises(VersionMasterVersionError):
                self.version_store.get_multi(keys)

    def test_get_multi_redis_error_1(self):
        self.redis_client.mget.side_effect = RedisError()

        with self.assertRaises(VersionGetError):
            self.version_store.get_multi([])

    def test_get_multi_redis_error_2(self):
        self.redis_client.mget.return_value = [None]
        self.redis_client.set.side_effect = RedisError()

        with self.assertRaises(VersionMasterVersionError):
            self.version_store.get_multi([])

    def test_get_multi_redis_error_3(self):
        self.redis_client.mget.return_value = [None]
        self.redis_client.get.side_effect = RedisError()

        with self.assertRaises(VersionMasterVersionError):
            self.version_store.get_multi([])

    def test_incr(self):
        self.version_store.incr('FOO')
        self.redis_client.incr.assert_called_once_with('FOO')

    def test_incr_redis_error(self):
        self.redis_client.incr.side_effect = RedisError()

        with self.assertRaises(VersionIncrementError):
            self.version_store.incr('FOO')

    def test_inhibit_caching(self):
        self.redis_client.mget.return_value = ['off']

        with self.assertRaises(CacheDisabled):
            self.version_store.get_multi([])
