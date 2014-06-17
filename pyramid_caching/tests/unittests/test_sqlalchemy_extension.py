import unittest

from pyramid.config import Configurator
from sqlalchemy import create_engine, Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base, DeferredReflection
from sqlalchemy.orm import scoped_session, sessionmaker

from pyramid_caching.interfaces import IIdentityInspector
from pyramid_caching.versioner import Versioner
from pyramid_caching.ext.sqlalchemy import register_sqlalchemy_caching


Base = declarative_base(cls=DeferredReflection)


class User(Base):
    __tablename__ = 'users'

    id = Column('id', Integer, primary_key=True)
    name = Column('name', String(100), primary_key=True)
    address = Column('address', String(100), nullable=False)


class Score(Base):
    __tablename__ = 'scores'

    id = Column('id', Integer, primary_key=True)
    user_id = Column('user_id', ForeignKey('users.id'))
    points = Column('points', Integer)


class SqlAlchemyExtensionTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        self.session = scoped_session(sessionmaker(bind=self.engine))
        Base.metadata.create_all(self.engine)
        Base.prepare(self.engine)

        user = User(id=1, name='hadrien', address='down the hill')
        self.session.add(user)
        self.session.commit()

        self.config = Configurator(settings={
            'caching.enabled': True,
            })
        register_sqlalchemy_caching(self.config, self.session, Base)

        self.config.registry.registerAdapter(lambda x: x,
                                             required=[str],
                                             provided=IIdentityInspector)
        self.config.registry.registerAdapter(lambda x: str(x),
                                             required=[unicode],
                                             provided=IIdentityInspector)
        self.key_versioner = DummyKeyVersioner()
        self.config.get_versioner = lambda: Versioner(self.key_versioner,
                                                      self.config)
        self.config.commit()

    def tearDown(self):
        Base.metadata.drop_all(self.engine)

    def test_create_entity(self):
        u = User(id=2, name='bob', address='123 street')
        self.session.add(u)
        self.session.commit()
        self.assertEqual(self.key_versioner.incr_keys, ['users'])

    def test_modify_entity(self):
        u = User(id=2, name='joe', address='123 street')
        self.session.add(u)
        self.session.commit()
        u.address = '456 moved'
        self.session.commit()
        self.assertItemsEqual(
            self.key_versioner.incr_keys,
            ['users', 'users:id=2:name=joe'])

    def test_delete_entity(self):
        user = self.session.query(User).filter_by(name='hadrien').first()
        self.session.delete(user)
        self.session.commit()
        self.assertItemsEqual(
            self.key_versioner.incr_keys,
            ['users', 'users:id=1:name=hadrien'])

    def test_add_to_collection(self):
        u = User(id=2, name='derek', address='1000 high rd')
        s = Score(id=1, user_id=u.id, points=25)
        self.session.add(u)
        self.session.add(s)
        self.session.commit()
        self.assertItemsEqual(
            self.key_versioner.incr_keys,
            ['users', 'scores:user_id=2'])


class DummyKeyVersioner:
    def __init__(self):
        self._incr_keys = set()

    def incr(self, key):
        self._incr_keys.add(key)

    @property
    def incr_keys(self):
        return list(self._incr_keys)
