import mock
import unittest

try:
    import pyramid_metrics
except ImportError:
    pyramid_metrics = None
from zope.interface import implementer

from pyramid_caching.interfaces import ISerializer
from pyramid_caching.tests.functional import Base as TestCase


@unittest.skipIf(pyramid_metrics is None, "requires pyramid_metrics")
class MetricsFunctionalTests(TestCase):
    def setUp(self):
        from example.model import User, Session
        registry = self.config.registry
        registry.registerUtility(TestSerializer(), ISerializer)
        self.app
        session = Session()
        session.add(User(id=1, name='Bob'))
        session.commit()

    @mock.patch('pyramid_metrics.utility.StatsClient')
    def test_cache_miss(self, m_stats_client):
        self.app.get('/users/1')
        m_incr = m_stats_client.return_value.incr
        stats_key = 'cache.miss.example.views:get_user'
        m_incr.assert_called_once_with(stats_key, count=1)

    @mock.patch('pyramid_metrics.utility.StatsClient')
    def test_cache_hit(self, m_stats_client):
        key_prefix = 'example.views:get_user'
        cache_key = key_prefix + ':user:user_id=1:v=0'
        self.cache_client.add(cache_key, "data")
        self.app.get('/users/1')
        m_incr = m_stats_client.return_value.incr
        m_incr.assert_called_once_with('cache.hit.' + key_prefix, count=1)

@implementer(ISerializer)
class TestSerializer(object):
    def loads(self, data):
        from pyramid.response import Response
        return Response()

    def dumps(self, data):
        return "data"
