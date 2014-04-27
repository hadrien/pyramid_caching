from pyramid.decorator import reify
from . import Base


class TestSqlAlchemyExt(Base):

    def setUp(self):
        self.app

    def tearDown(self):
        from example.model import User
        for user in self.sqla_session.query(User).all():
            self.sqla_session.delete(user)
        self.sqla_session.commit()

    @reify
    def sqla_session(self):
        from example.model import Session
        session = Session()
        self.addCleanup(session.close)
        self.addCleanup(delattr, self, 'sqla_session')
        return session

    def test_incr(self):
        from example.model import User
        user = User()

        key_cls_0 = self.model_versioner.get_key(User)
        key_obj_0 = self.model_versioner.get_key(user)

        self.model_versioner.incr(user)

        key_cls_1 = self.model_versioner.get_key(User)
        key_obj_1 = self.model_versioner.get_key(user)

        self.assertNotEqual(key_cls_1, key_cls_0)
        self.assertNotEqual(key_obj_1, key_obj_0)

    def test_unicity_simple_pk(self):
        from example.model import User

        user0 = User(name=u'Bob Marley')
        user1 = User(name=u'Peter Tosh')

        self.sqla_session.add(user0)
        self.sqla_session.add(user1)
        self.sqla_session.commit()

        self.assertNotEqual(
            self.model_versioner.get_key(user0),
            self.model_versioner.get_key(user1),
            )

    def test_unicity_composite_pk(self):
        from example.model import User, UserNote

        msg0 = UserNote(id=11, content='I ray')
        msg1 = UserNote(id=22, content='Jah')
        user = User(name=u'Bob Marley')

        user.notes = [msg0, msg1]

        self.sqla_session.add(user)
        self.sqla_session.commit()

        self.assertNotEqual(
            self.model_versioner.get_key(msg0),
            self.model_versioner.get_key(msg1),
            )

    def test_auto_incr(self):
        from example.model import User, UserNote

        user = User(name=u'Bob')

        self.sqla_session.add(user)

        self.sqla_session.commit()

        key_user_v0 = self.model_versioner.get_key(user)

        user.name = 'Bob Marley'

        self.sqla_session.commit()

        key_user_v1 = self.model_versioner.get_key(user)

        self.assertNotEqual(key_user_v0, key_user_v1)
