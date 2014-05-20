import cPickle as pickle
from cStringIO import StringIO

from pyramid.response import Response
from zope.interface import implementer

from pyramid_caching.interfaces import ISerializer, ISerializationAdapter

SERIALIZER_META_VERSION = 1
PICKLE_PROTOCOL = 2


def includeme(config):
    registry = config.registry

    utility = SerializerUtility(registry)
    registry.registerUtility(utility)

    utility.register_serialization_adapter(Response, ResponseAdapter)

    config.add_directive('get_serializer', get_serializer, action_wrap=False)


def get_serializer(config):
    return config.registry.getUtility(ISerializer)


class DeserializationError(Exception):
    """An error that occurs when valid cached data could not be decoded."""


@implementer(ISerializer)
class SerializerUtility(object):
    def __init__(self, registry):
        self.registry = registry

    def register_serialization_adapter(self, object_class, adapter_factory):
        # Register serializer by object class.
        self.registry.registerAdapter(lambda x: adapter_factory(),
                                      required=[object_class],
                                      provided=ISerializationAdapter,
                                      )
        # Register deserializer by type name.
        self.registry.registerAdapter(lambda x: adapter_factory(),
                                      required=[None],
                                      provided=ISerializationAdapter,
                                      name=adapter_factory.name,
                                      )

    def dumps(self, obj, adapter=None):
        if adapter is None:
            adapter = self.registry.queryAdapter(obj, ISerializationAdapter)
        f = StringIO()
        pickler = pickle.Pickler(f, PICKLE_PROTOCOL)
        meta = {
            'type': adapter.name,
            'version': SERIALIZER_META_VERSION,
            }
        payload = adapter.serialize(obj)
        pickler.dump(meta)
        pickler.dump(payload)
        return f.getvalue()

    def loads(self, data):
        f = StringIO(data)
        unpickler = pickle.Unpickler(f)
        meta = unpickler.load()
        if 'version' not in meta or meta['version'] != SERIALIZER_META_VERSION:
            return None
        adapter = self.registry.queryAdapter(None,
                                             ISerializationAdapter,
                                             name=meta['type'])
        if adapter is None:
            raise DeserializationError("No decoder registered for type=%s",
                                       meta['type'])
        payload = unpickler.load()
        return adapter.deserialize(payload)


@implementer(ISerializationAdapter)
class ResponseAdapter(object):
    """Deserializer for Pyramid Response objects."""

    name = 'pyramid.response.Response'

    def serialize(self, response):
        return str(response)

    def deserialize(self, raw_response):
        return Response.from_file(StringIO(raw_response))
