from pyramid_caching.tests.functional import Base


class Test(Base):

    def setUp(self):
        # creating app to setup cache and decorate stuff.
        self.app

        from example.model import User, Session
        session = Session()
        session.add(User(id=1, name='Bob'))
        session.commit()

    def test_cache_basic(self):
        from example.views import fibonacci

        self.assertEqual({}, self.cache_client.cache)
        self.assertEqual({}, self.versioner.key_versioner.versions)

        fibonacci(10)

        cache = {
            'fibonacci:n=0:v=0': 0,
            'fibonacci:n=1:v=0': 1,
            'fibonacci:n=2:v=0': 1,
            'fibonacci:n=3:v=0': 2,
            'fibonacci:n=4:v=0': 3,
            'fibonacci:n=5:v=0': 5,
            'fibonacci:n=6:v=0': 8,
            'fibonacci:n=7:v=0': 13,
            'fibonacci:n=8:v=0': 21,
            'fibonacci:n=9:v=0': 34,
            'fibonacci:n=10:v=0': 55,
            }

        self.assertEqual(cache, self.cache_client.cache)

        versions = {
            'version:n=0': 0,
            'version:n=1': 0,
            'version:n=2': 0,
            'version:n=3': 0,
            'version:n=4': 0,
            'version:n=5': 0,
            'version:n=6': 0,
            'version:n=7': 0,
            'version:n=8': 0,
            'version:n=9': 0,
            'version:n=10': 0,
        }

        self.assertEqual(versions, self.versioner.key_versioner.versions)

    def test_cache_view(self):
        self.app.get('/users/1')
        self.app.get('/users/1')
        self.app.get('/users/1')

