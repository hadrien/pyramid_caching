import unittest

from pyramid.config import Configurator
from sqlalchemy import create_engine, Column, Integer, MetaData, String, Table
from sqlalchemy.orm import clear_mappers, mapper, scoped_session, sessionmaker
from zope.interface import implementer

from pyramid_caching.interfaces import IIdentityInspector
from pyramid_caching.versioner import Versioner
from pyramid_caching.ext.sqlalchemy import register_sqla_session_caching_hook

engine = create_engine('sqlite:///:memory:')
metadata = MetaData(engine)

Session = scoped_session(sessionmaker())
Session.configure(bind=engine)


class SqlAlchemyExtensionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        users = Table('users', metadata,
                      Column('id', Integer, primary_key=True),
                      Column('name', String(100), nullable=False),
                      Column('address', String(100), nullable=False),
                      )
        metadata.create_all()
        mapper(User, users)

    def setUp(self):
        self.config = Configurator(settings={
            'caching.enabled': True,
            })
        register_sqla_session_caching_hook(self.config, Session)
        self.config.registry.registerAdapter(DummyIdentityInspector(),
                                             required=[User],
                                             provided=IIdentityInspector)
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
        Session.close_all()

    @classmethod
    def tearDownClass(cls):
        clear_mappers()

    def test_create_entity(self):
        u = User(name='bob', address='123 street')
        Session.add(u)
        Session.commit()
        self.assertEqual(self.key_versioner.incr_keys, ['users'])

    def test_modify_entity(self):
        u = User(name='joe', address='123 street')
        Session.add(u)
        Session.commit()
        u.address = '456 moved'
        Session.commit()
        self.assertEqual(self.key_versioner.incr_keys, ['users', 'users:joe'])


class User(object):
    __tablename__ = 'users'

    def __init__(self, name, address):
        self.name = name
        self.address = address


@implementer(IIdentityInspector)
class DummyIdentityInspector:
    def __call__(self, entity):
        return entity.__tablename__ + ':' + entity.name


class DummyKeyVersioner:
    def __init__(self):
        self._incr_keys = set()

    def incr(self, key):
        self._incr_keys.add(key)

    @property
    def incr_keys(self):
        return list(self._incr_keys)
