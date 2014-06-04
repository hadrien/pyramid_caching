import inspect
import unittest

from nose_parameterized import parameterized
from zope.interface import implementer

from pyramid_caching.interfaces import IIdentityInspector
from pyramid_caching.versioner import Versioner


class BasicModel(object):
    def __init__(self, id):
        self.id = id

    def __hash__(self):
        return self.id


@implementer(IIdentityInspector)
class BasicModelIdentityInspector(object):

    def _get_cls_identity(self, cls):
        return '%s.%s' % (cls.__module__, cls.__name__)

    def _get_obj_identity(self, obj):
        return '%s.id_%s' % (self._get_cls_identity(obj.__class__), hash(obj))

    def identify(self, obj_or_cls):
        if inspect.isclass(obj_or_cls):
            identity = self._get_cls_identity(obj_or_cls)
        else:
            identity = self._get_obj_identity(obj_or_cls)

        return identity


def get_basic():
    def instantiate_model(id=4):
        return BasicModel(id)

    class TestKeyVersioner(object):
        def __init__(self):
            self._d = dict()

        def get_multi(self, keys):
            return [(k, self._d.setdefault(k, 0)) for k in keys]

        def incr(self, key):
            self._d[key] += 1
    key_versioner = TestKeyVersioner()

    id_inspector = BasicModelIdentityInspector()

    versioner = Versioner(key_versioner, None, identify=id_inspector.identify)
    return versioner, instantiate_model, BasicModel


class TestBasic(unittest.TestCase):

    @parameterized.expand([
        ("with_basic_impl", get_basic),
    ])
    def test_get_multi_keys(self, test_name, test_fixture_func):
        result = test_fixture_func()
        versioner, model_factory, model_cls = result

        model1 = model_factory(id=42)
        model2 = model_factory(id=43)
        model3 = model_factory(id=44)

        result = versioner.get_multi_keys(
            [model1, model2, model3, model_cls]
        )

        expected = [
            'pyramid_caching.tests.unittests.test_versioners.BasicModel.id_42:v=0',
            'pyramid_caching.tests.unittests.test_versioners.BasicModel.id_43:v=0',
            'pyramid_caching.tests.unittests.test_versioners.BasicModel.id_44:v=0',
            'pyramid_caching.tests.unittests.test_versioners.BasicModel:v=0',
        ]

        self.assertEqual(result, expected)

    @parameterized.expand([
        ("basic", get_basic),
    ])
    def test_incr(self, test_name, test_fixture_func):
        result = test_fixture_func()
        versioner, model_factory, model_cls = result

        model1 = model_factory()

        key_cls_v0 = versioner.get_multi_keys([model_cls])
        key_id1_v0 = versioner.get_multi_keys([model1])

        versioner.incr(model1)
        versioner.incr(model_cls)

        key_id1_v1 = versioner.get_multi_keys([model1])
        key_cls_v1 = versioner.get_multi_keys([model_cls])

        self.assertNotEqual(key_id1_v0, key_id1_v1)
        self.assertNotEqual(key_cls_v0, key_cls_v1)
