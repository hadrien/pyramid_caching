from pyramid.decorator import reify
from . import Base


class Test(Base):
    def setUp(self):
        # creating app to setup sqla session.
        self.app

    def tearDown(self):
        from example.model import User
        for user in self.sqla_session.query(User).all():
            self.sqla_session.delete(user)
        try:
            self.sqla_session.commit()
        except:  # pragma no cover
            pass

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

        key_cls_0 = self.versioner.get_multi_keys([User])
        key_obj_0 = self.versioner.get_multi_keys([user])

        self.versioner.incr(User)
        self.versioner.incr(user)

        key_cls_1 = self.versioner.get_multi_keys([User])
        key_obj_1 = self.versioner.get_multi_keys([user])

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
            self.versioner.get_multi_keys([user0]),
            self.versioner.get_multi_keys([user1]),
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
            self.versioner.get_multi_keys([msg0]),
            self.versioner.get_multi_keys([msg1]),
            )

    def test_auto_incr(self):
        from example.model import User, UserNote

        # create user and user notes
        user = User(id=1, name=u'Bob')
        msg0 = UserNote(id=11, content='I ray')
        msg1 = UserNote(id=22, content='Jah')
        user.notes = [msg0, msg1]

        self.sqla_session.add(user)

        self.sqla_session.commit()

        key_user_v0 = self.versioner.get_multi_keys([user])
        key_msg0_v0 = self.versioner.get_multi_keys([msg0])
        key_msg1_v0 = self.versioner.get_multi_keys([msg1])

        # modify user and msg0
        user.name = 'Bob Marley'
        msg0.content = 'I RAY'

        self.sqla_session.commit()

        key_user_v1 = self.versioner.get_multi_keys([user])
        key_msg0_v1 = self.versioner.get_multi_keys([msg0])

        # keys are automaticaly changed
        self.assertNotEqual(key_user_v0, key_user_v1)
        self.assertNotEqual(key_msg0_v0, key_msg0_v1)
        # not msg1
        self.assertEqual(key_msg1_v0, self.versioner.get_multi_keys([msg1]))

        # we can get a key via a new object instance
        self.assertEqual(
            key_msg0_v1,
            self.versioner.get_multi_keys([UserNote(id=11, user_id=user.id)]),
            )

        user = self.sqla_session.query(User).get(1)
        # remove msg0
        user.notes.pop(0)
        user_id = user.id
        self.sqla_session.commit()

        # msg0 key has changed
        key_msg0_v2 = self.versioner.get_multi_keys([UserNote(id=11,
                                                    user_id=user_id)])
        self.assertNotEqual(key_msg0_v1, key_msg0_v2)

        # delete user which cascade delete msg1
        user = self.sqla_session.query(User).get(1)
        self.sqla_session.delete(user)
        self.sqla_session.commit()

        self.assertNotEqual(key_user_v1,
                            self.versioner.get_multi_keys([user]))

        self.assertNotEqual(key_msg1_v0, self.versioner.get_multi_keys([msg1]))
