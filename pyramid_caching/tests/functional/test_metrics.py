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

    @mock.patch('pyramid_caching.ext.metrics.get_current_metrics')
    def test_cache_miss(self, m_metrics):
        self.app.get('/users/1')
        m_incr = m_metrics.return_value.incr
        m_incr.assert_called_once_with(
            ('cache.miss', 'example.views:get_user'))

    @mock.patch('pyramid_caching.ext.metrics.get_current_metrics')
    def test_cache_hit(self, m_metrics):
        self.app.get('/users/1')
        self.app.get('/users/1')
        m_incr = m_metrics.return_value.incr
        m_incr.assert_has_calls([
            mock.call(('cache.miss', 'example.views:get_user')),
            mock.call(('cache.hit', 'example.views:get_user')),
            ])


@implementer(ISerializer)
class TestSerializer(object):
    def loads(self, data):
        from pyramid.response import Response
        return Response()

    def dumps(self, data):
        return "data"
