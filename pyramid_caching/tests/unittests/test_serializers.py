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
        data = pickle.loads(data)
        self.assertEqual(data['type'], "dummy")

    def test_encode_meta_format_version(self):
        utility = SerializerUtility(DummyRegistry())
        data = utility.dumps("object", adapter=DummyAdapter())
        data = pickle.loads(data)
        self.assertEqual(data['version'], SERIALIZER_META_VERSION)

    def _create_data(self,
                     meta_type=DummyAdapter.name,
                     meta_version=SERIALIZER_META_VERSION,
                     payload="OBJECT"):
        data = {
            'type': meta_type,
            'version': meta_version,
            'payload': payload,
            }
        return pickle.dumps(data, protocol=PICKLE_PROTOCOL)

    def test_invalid_meta_format_version(self):
        utility = SerializerUtility(DummyRegistry())
        data = self._create_data(meta_version=9999)
        self.assertIsNone(utility.loads(data))

    def test_encode_payload(self):
        utility = SerializerUtility(DummyRegistry())
        data = utility.dumps("object", adapter=DummyAdapter())
        data = pickle.loads(data)
        self.assertEqual(data['payload'], "OBJECT")

    def test_register_serializer(self):
        utility = SerializerUtility(self.config.registry)
        utility.register_serialization_adapter(str, DummyAdapter)
        data = utility.dumps("object")
        data = pickle.loads(data)
        self.assertEqual(data['type'], "dummy")

    def test_query_serializer(self):
        utility = SerializerUtility(self.config.registry)
        utility.register_serialization_adapter(str, DummyAdapter)
        data = utility.dumps("object")
        data = pickle.loads(data)
        self.assertEqual(data['payload'], "OBJECT")

    def test_query_deserializer(self):
        utility = SerializerUtility(self.config.registry)
        utility.register_serialization_adapter(str, DummyAdapter)
        data = self._create_data()
        obj = utility.loads(data)
        self.assertEqual(obj, "object")

    def test_missing_deserializer(self):
        from pyramid_caching.serializers import DeserializationError
        utility = SerializerUtility(self.config.registry)
        data = {
            'type': 'alien',
            'version': SERIALIZER_META_VERSION,
            'payload': "oBjEcT",
            }
        data = pickle.dumps(data, protocol=PICKLE_PROTOCOL)
        with self.assertRaises(DeserializationError):
            utility.loads(data)

    def test_missing_serializer(self):
        from pyramid_caching.serializers import SerializationError
        utility = SerializerUtility(self.config.registry)

        class UnknownType:
            pass

        with self.assertRaises(SerializationError):
            utility.dumps(UnknownType())
