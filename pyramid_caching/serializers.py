import cPickle as pickle
from cStringIO import StringIO

from pyramid.response import Response
from zope.interface import implementer, providedBy

from pyramid_caching.exc import SerializationError, DeserializationError
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
            if adapter is None:
                raise SerializationError(
                    "No encoder registered for %s" % providedBy(obj).__name__)

        meta = {
            'type': adapter.name,
            'version': SERIALIZER_META_VERSION,
            'payload': adapter.serialize(obj),
            }

        return pickle.dumps(meta, protocol=PICKLE_PROTOCOL)

    def loads(self, data):
        data = pickle.loads(data)
        if 'version' not in data or data['version'] != SERIALIZER_META_VERSION:
            return None
        adapter = self.registry.queryAdapter(None,
                                             ISerializationAdapter,
                                             name=data['type'])
        if adapter is None:
            raise DeserializationError("No decoder registered for type=%s",
                                       data['type'])
        return adapter.deserialize(data['payload'])


@implementer(ISerializationAdapter)
class ResponseAdapter(object):
    """Deserializer for Pyramid Response objects."""

    name = 'pyramid.response.Response'

    def serialize(self, response):
        return str(response)

    def deserialize(self, raw_response):
        res = Response.from_file(StringIO(raw_response))

        # Workaround for issue #99 in webob. All header names must be str
        # instances.
        res._headerlist = [(str(k), str(v)) for k, v in res._headerlist]

        return res
