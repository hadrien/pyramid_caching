import inspect
import unittest

from nose_parameterized import parameterized
from zope.interface import implementer

from pyramid_caching.interfaces import IIdentityInspector
from pyramid_caching.versioners import Versioner

from pyramid_caching.ext.redis import RedisVersionWrapper

from fakeredis import FakeStrictRedis


class BasicModel(object):
    pass


@implementer(IIdentityInspector)
class BasicModelIdentityInspector(object):

    def _get_cls_identity(self, cls):
        return '%s.%s' % (cls.__module__, cls.__name__)

    def _get_obj_identity(self, obj):
        return '%s.id_%s' % (self._get_cls_identity(obj.__class__), id(obj))

    def identify(self, obj_or_cls):
        if inspect.isclass(obj_or_cls):
            identity = self._get_cls_identity(obj_or_cls)
        else:
            identity = self._get_obj_identity(obj_or_cls)

        return identity


def get_basic():
    def instantiate_model():
        return BasicModel()

    key_versioner = RedisVersionWrapper(FakeStrictRedis())

    id_inspector = BasicModelIdentityInspector()
    versioner = Versioner(key_versioner, id_inspector.identify)
    return key_versioner, versioner, instantiate_model, BasicModel


class TestBasic(unittest.TestCase):

    @parameterized.expand([
        ("with_basic_impl", get_basic),
    ])
    def test_get_multi_keys(self, test_name, test_fixture_func):
        result = test_fixture_func()
        key_versioner, versioner, model_factory, model_cls = result

        model1 = model_factory()
        model2 = model_factory()
        model3 = model_factory()

        result1 = versioner.get_multi_keys(
            [model1, model2, model3, model_cls]
        )

        result2 = [
            versioner.get_key(model1),
            versioner.get_key(model2),
            versioner.get_key(model3),
            versioner.get_key(model_cls),
        ]

        self.assertEqual(result1, result2)

    @parameterized.expand([
        ("basic", get_basic),
    ])
    def test_incr(self, test_name, test_fixture_func):
        result = test_fixture_func()
        key_versioner, versioner, model_factory, model_cls = result

        model1 = model_factory()

        key_cls_v0 = versioner.get_key(model_cls)
        key_id1_v0 = versioner.get_key(model1)

        versioner.incr(model1)

        key_id1_v1 = versioner.get_key(model1)
        key_cls_v1 = versioner.get_key(model_cls)

        self.assertNotEqual(key_id1_v0, key_id1_v1)
        self.assertNotEqual(key_cls_v0, key_cls_v1)
