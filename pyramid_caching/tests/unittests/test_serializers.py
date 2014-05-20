from cStringIO import StringIO
import pickle
import unittest

from pyramid import testing

from pyramid_caching.serializers import (
    PICKLE_PROTOCOL,
    SerializerUtility,
    SERIALIZER_META_VERSION,
    )


class DummyRegistry(object):
    def queryAdapter(self, object, interface, name=None, default=None):
        # Utility should not query registry when passed an adapter.
        raise AssertionError()


class DummyAdapter(object):
    name = "dummy"

    def serialize(self, obj):
        return obj.upper()

    def deserialize(self, data):
        return data.lower()


class TestSerializers(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_implements_interface(self):
        from zope.interface.verify import verifyClass
        from pyramid_caching.interfaces import ISerializer
        verifyClass(ISerializer, SerializerUtility)

    def test_encode_serializer_type(self):
        utility = SerializerUtility(DummyRegistry())
        data = utility.dumps("object", adapter=DummyAdapter())
        meta = pickle.loads(data)
        self.assertEqual(meta['type'], "dummy")

    def test_encode_meta_format_version(self):
        utility = SerializerUtility(DummyRegistry())
        data = utility.dumps("object", adapter=DummyAdapter())
        meta = pickle.loads(data)
        self.assertEqual(meta['version'], SERIALIZER_META_VERSION)

    def _create_data(self,
                     meta_type=DummyAdapter.name,
                     meta_version=SERIALIZER_META_VERSION,
                     payload="OBJECT"):
        f = StringIO()
        pickler = pickle.Pickler(f, PICKLE_PROTOCOL)
        meta = {
            'type': meta_type,
            'version': meta_version,
            }
        pickler.dump(meta)
        pickler.dump(payload)
        return f.getvalue()

    def test_invalid_meta_format_version(self):
        utility = SerializerUtility(DummyRegistry())
        data = self._create_data(meta_version=9999)
        self.assertIsNone(utility.loads(data))

    def test_encode_payload(self):
        utility = SerializerUtility(DummyRegistry())
        data = utility.dumps("object", adapter=DummyAdapter())
        f = StringIO(data)
        unpickler = pickle.Unpickler(f)
        unpickler.load()
        payload = unpickler.load()
        self.assertEqual(payload, "OBJECT")

    def test_register_serializer(self):
        utility = SerializerUtility(self.config.registry)
        utility.register_serialization_adapter(str, DummyAdapter)
        data = utility.dumps("object")
        meta = pickle.loads(data)
        self.assertEqual(meta['type'], "dummy")

    def test_query_serializer(self):
        utility = SerializerUtility(self.config.registry)
        utility.register_serialization_adapter(str, DummyAdapter)
        data = utility.dumps("object")
        f = StringIO(data)
        unpickler = pickle.Unpickler(f)
        unpickler.load()
        payload = unpickler.load()
        self.assertEqual(payload, "OBJECT")

    def test_query_deserializer(self):
        utility = SerializerUtility(self.config.registry)
        utility.register_serialization_adapter(str, DummyAdapter)
        data = self._create_data()
        obj = utility.loads(data)
        self.assertEqual(obj, "object")

    def test_missing_deserializer(self):
        from pyramid_caching.serializers import DeserializationError
        utility = SerializerUtility(self.config.registry)
        f = StringIO()
        meta = {
            'type': 'alien',
            'version': SERIALIZER_META_VERSION,
            }
        payload = "oBjEcT"
        p = pickle.Pickler(f, 1)
        p.dump(meta)
        p.dump(payload)
        data = f.getvalue()
        with self.assertRaises(DeserializationError):
            utility.loads(data)
