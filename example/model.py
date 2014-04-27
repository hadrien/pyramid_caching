
from sqlalchemy import Column, Integer, String, MetaData, ForeignKey, Text
from sqlalchemy.engine import engine_from_config
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

metadata = MetaData()

Base = declarative_base(metadata=metadata)
Session = sessionmaker()


def includeme(config):
    config.include('pyramid_caching.ext.sqlalchemy')
    engine = engine_from_config(config.registry.settings)
    metadata.create_all(engine)
    Session.configure(bind=engine)

    config.register_sqla_session_caching_hook(Session)
    config.register_sqla_base_class(Base)


class User(Base):

    __tablename__ = 'user'

    id = Column('id', Integer, primary_key=True)

    name = Column('name', String(32))

    notes = relationship('UserNote', backref='user', cascade='delete')


class UserNote(Base):

    __tablename__ = 'user_note'

    user_id = Column('user_id', ForeignKey('user.id'),
                     primary_key=True)

    id = Column('id', Integer, primary_key=True, autoincrement=True)

    content = Column('name', Text())
