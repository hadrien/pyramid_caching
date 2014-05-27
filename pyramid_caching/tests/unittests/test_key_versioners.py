import unittest

import mock
from nose_parameterized import parameterized


from pyramid_caching.ext.redis import RedisVersionWrapper

from redis import StrictRedis

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
