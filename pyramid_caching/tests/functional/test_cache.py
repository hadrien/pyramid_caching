from pyramid_caching.tests.functional import Base


class Test(Base):

    def setUp(self):
        # creating app to setup cache and decorate stuff.
        self.app
        from example.model import User, Session
        session = Session()
        session.add(User(id=1, name='Bob'))
        session.commit()

        self.cache_client.client.delete('cache')

    def tearDown(self):
        self.cache_client.client.delete('cache')

    def test_cache_view(self):
        self.app.get('/users/1')
        self.app.get('/users/1')
        self.app.get('/users/1')

        # TODO: test if cache was enabled

    def test_inhibited_cache_view(self):
        self.key_versioner_client.client.set('cache', 'off')

        self.app.get('/users/1')
        self.app.get('/users/1')
        self.app.get('/users/1')

        # TODO: test if cache was disabled
