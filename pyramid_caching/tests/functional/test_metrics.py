import mock

from zope.interface import implementer

from pyramid_caching.interfaces import ISerializer
from pyramid_caching.tests.functional import Base as TestCase


class MetricsFunctionalTests(TestCase):
    def setUp(self):
        from example.model import User, Session
        registry = self.config.registry
        registry.registerUtility(TestSerializer(), ISerializer)
        self.app
        session = Session()
        session.add(User(id=1, name='Bob'))
        session.commit()

    def tearDown(self):
        from example.model import Session
        Session.remove()

    @mock.patch('pyramid_metrics.utility.StatsClient')
    def test_cache_miss(self, m_statsd):
        self.app.get('/users/1')
        m_incr = m_statsd.return_value.incr
        m_incr.assert_called_once_with(
            'cache.miss.example.views:get_user', count=1)

    @mock.patch('pyramid_metrics.utility.StatsClient')
    def test_cache_hit(self, m_statsd):
        self.app.get('/users/1')
        self.app.get('/users/1')

        m_incr = m_statsd.return_value.incr
        m_incr.assert_has_calls([
            mock.call('cache.miss.example.views:get_user', count=1),
            mock.call('cache.hit.example.views:get_user', count=1),
            ])


@implementer(ISerializer)
class TestSerializer(object):
    def loads(self, data):
        from pyramid.response import Response
        return Response()

    def dumps(self, data):
        return "data"
