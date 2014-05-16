from pyramid_caching.tests.functional import Base


class Test(Base):

    def setUp(self):
        # creating app to setup cache and decorate stuff.
        self.app
        from example.model import User, Session
        session = Session()
        session.add(User(id=1, name='Bob'))
        session.commit()

    def test_cache_view(self):
        self.app.get('/users/1')
        self.app.get('/users/1')
        self.app.get('/users/1')
