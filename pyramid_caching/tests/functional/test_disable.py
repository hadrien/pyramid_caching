import os

from pyramid_caching.tests.functional import Base


class Test(Base):

    def setUp(self):
        os.environ['CACHING_ENABLED'] = 'false'

        # creating app to setup cache and decorate stuff.
        self.app
        from example.model import User, Session
        session = Session()
        session.add(User(id=1, name='Bob'))
        session.commit()

    def tearDown(self):
        from example.model import Session
        os.environ.pop('CACHING_ENABLED', None)
        Session.remove()

    def test_disabled_api(self):
        # Check that part of the API is available (inactive)

        self.assertFalse(self.config.registry.settings['caching.enabled'])

        self.assertTrue(
            hasattr(self.config, 'register_sqla_session_caching_hook'))
        self.assertTrue(
            hasattr(self.config, 'register_sqla_base_class'))

    def test_disabled_cache_view(self):
        self.app.get('/users/1')
        self.app.get('/users/1')
        self.app.get('/users/1')
