import inspect
import logging

from zope.interface import implementer

from pyramid_caching.interfaces import (
    IIdentityInspector,
    IKeyVersioner,
    IVersioner,
    )

log = logging.getLogger(__name__)


def includeme(config):
    registry = config.registry

    def identify(model_obj_or_cls):
        return registry.queryAdapter(model_obj_or_cls, IIdentityInspector)

    registry.registerAdapter(lambda x: x, required=[str],
                             provided=IIdentityInspector)

    registry.registerAdapter(lambda x: str(x), required=[unicode],
                             provided=IIdentityInspector)

    registry.registerAdapter(lambda x: str(x), required=[int],
                             provided=IIdentityInspector)

    registry.registerAdapter(lambda x: str(x), required=[float],
                             provided=IIdentityInspector)

    registry.registerAdapter(
        lambda x: TupleIdentityInspector(identify).identify(x),
        required=[tuple],
        provided=IIdentityInspector,
        )

    registry.registerAdapter(
        lambda x: DictIdentityInspector(identify).identify(x),
        required=[dict],
        provided=IIdentityInspector,
        )

    key_versioner = MemoryKeyVersioner()

    versioner = Versioner(key_versioner, identify)

    config.registry.registerUtility(versioner)
    config.add_directive('get_versioner', get_versioner, action_wrap=False)
    config.add_request_method(get_versioner, 'versioner', reify=True)


def get_versioner(config_or_request):
    return config_or_request.registry.getUtility(IVersioner)


@implementer(IIdentityInspector)
class TupleIdentityInspector(object):

    def __init__(self, identify):
        self._identify = identify

    def identify(self, tuple_or_list):
        return ':'.join([self._identify(elem) for elem in tuple_or_list])


@implementer(IIdentityInspector)
class DictIdentityInspector(object):

    def __init__(self, identify):
        self._identify = identify

    def identify(self, dict_like):
        elems = ['%s=%s' % (self._identify(k), self._identify(v))
                 for k, v in dict_like.iteritems()]
        return ':'.join(elems)


@implementer(IKeyVersioner)
class MemoryKeyVersioner(object):
    """Highly inefficient in-memory key store as a proof of concept.
    It can be used in tests.

    Do not use in production.
    """

    def __init__(self):
        self.versions = dict()

    def _format(self, key):
        return 'version:%s' % key

    def get(self, key, default=0):
        return self.versions.setdefault(self._format(key), default)

    def get_multi(self, keys, default=0):
        return [self.get(key, default) for key in keys]

    def incr(self, key, start=0):
        k = self._format(key)
        version = self.versions.get(k, start) + 1
        log.debug('incrementing to version=%s key=%s', version, key)
        self.versions[k] = version


@implementer(IVersioner)
class Versioner(object):

    def __init__(self, key_versioner, identify):
        self.key_versioner = key_versioner
        self.identify = identify

    def get_key(self, anything):
        identity = self.identify(anything)
        return '%s:v=%s' % (identity, self.key_versioner.get(identity))

    def get_multi_keys(self, things):
        keys = [self.identify(anything) for anything in things]

        versions = self.key_versioner.get_multi(keys)

        return ['%s:v=%s' % (key, version)
                for (key, version) in zip(keys, versions)]

    def incr(self, obj_or_cls, start=0):
        self.key_versioner.incr(self.identify(obj_or_cls))

        if not inspect.isclass(obj_or_cls):  # increment model class version
            identity = self.identify(obj_or_cls.__class__)
            self.key_versioner.incr(identity)
