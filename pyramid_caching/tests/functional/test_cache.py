from pyramid_caching.tests.functional import Base


class Test(Base):

    def setUp(self):
        # creating app to setup cache and decorate stuff.
        self.app
        from example.model import User, Session
        session = Session()
        session.add(User(id=1, name='Bob'))
        session.commit()
        session.close()

        self.cache_client.client.delete('cache')

    def tearDown(self):
        self.cache_client.client.delete('cache')

    def test_cache_view(self):
        result1 = self.app.get('/users/1').json

        result2 = self.app.get('/users/1').json

        self.assertEqual(result1, result2)

        from example.model import User, Session
        session = Session()
        user = session.query(User).get(1)
        user.name = 'Bob Marley'
        session.commit()
        session.close()
        self.assertNotEqual(result1, self.app.get('/users/1').json)

    def test_inhibited_cache_view(self):
        self.key_versioner_client.client.set('cache', 'off')

        self.app.get('/users/1')
        self.app.get('/users/1')
        self.app.get('/users/1')

        # TODO: test if cache was disabled
