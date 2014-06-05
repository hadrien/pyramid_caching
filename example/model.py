from sqlalchemy import Column, Integer, String, MetaData, ForeignKey, Text
from sqlalchemy.engine import engine_from_config
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker, relationship

metadata = MetaData()

session_factory = sessionmaker()
Session = scoped_session(session_factory)


def includeme(config):
    config.include('pyramid_caching.ext.sqlalchemy')
    engine = engine_from_config(config.registry.settings)
    metadata.create_all(engine)
    Session.configure(bind=engine)

    config.register_sqla_session_caching_hook(Session)
    config.register_sqla_base_class(Base)

    config.scan(__name__)


class Base(declarative_base(metadata=metadata)):
    __abstract__ = True

    @classmethod
    def all(cls):
        return Session().query(cls).all()

    @classmethod
    def get(cls, ids):
        return Session().query(cls).get(ids)


class User(Base):

    __tablename__ = 'user'

    id = Column('id', Integer, primary_key=True)

    name = Column('name', String(32))

    notes = relationship('UserNote', backref='user',
                         cascade='all, delete-orphan')

    @classmethod
    def filter_by_name(cls, name):
        return Session().query(cls).filter_by(name=name).all()

    def __repr__(self):
        return '<User id=%s>' % self.id


class UserNote(Base):

    __tablename__ = 'user_note'

    id = Column('id', Integer, primary_key=True, autoincrement=True)

    user_id = Column('user_id', ForeignKey('user.id', ondelete='cascade'),
                     primary_key=True)

    content = Column('name', Text())

    def __repr__(self):
        return '<UserNote id=%2s user_id=%s>' % (self.id, self.user_id)
