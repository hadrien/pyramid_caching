import cPickle as pickle
from StringIO import StringIO

from pyramid.response import Response
from zope.interface import implementer

from pyramid_caching.interfaces import ISerializer


def includeme(config):
    registry = config.registry

    utility = Utility(registry)
    registry.registerUtility(utility)

    response_serializer = ResponseSerializer()
    # to get response_serializer with a Response object
    registry.registerAdapter(lambda x: response_serializer,
                             required=[Response],
                             provided=ISerializer,
                             )
    # to get response_serializer by name
    registry.registerAdapter(lambda x: response_serializer,
                             required=[None],
                             provided=ISerializer,
                             name=response_serializer.name,
                             )

    config.add_directive('get_serializer', get_serializer, action_wrap=False)


def get_serializer(config_or_request):
    return config_or_request.registry.getUtility(ISerializer)


@implementer(ISerializer)
class Utility(object):

    name = ''

    def __init__(self, registry):
        self.queryAdapter = registry.queryAdapter

    def serialize(self, obj):
        serializer = self.queryAdapter(obj, ISerializer)
        return pickle.dumps({
            'type': serializer.name,
            'payload': serializer.serialize(obj),
        })

    def deserialize(self, data):
        data_dict = pickle.loads(data)
        serializer = self.queryAdapter(None, ISerializer,
                                       name=data_dict['type'])
        return serializer.deserialize(data_dict['payload'])


@implementer(ISerializer)
class ResponseSerializer(object):

    name = 'pyramid.response.Response'

    def serialize(self, response):
        return str(response)

    def deserialize(self, raw_response):
        return Response.from_file(StringIO(raw_response))
