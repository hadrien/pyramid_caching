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

    str_unicode_inspector = StrUnicodeIdentityInspector()

    registry.registerAdapter(lambda _: str_unicode_inspector, required=[str],
                             provided=IIdentityInspector)

    registry.registerAdapter(lambda _: str_unicode_inspector,
                             required=[unicode],
                             provided=IIdentityInspector)

    def identify(model_obj_or_cls, ids=None):
        inspector = registry.queryAdapter(model_obj_or_cls, IIdentityInspector)
        if inspector is None:
            return None
        return inspector.identify(model_obj_or_cls, ids)

    tuple_inspector = TupleIdentityInspector(identify)

    registry.registerAdapter(lambda _: tuple_inspector,
                             required=[tuple],
                             provided=IIdentityInspector)

    key_versioner = MemoryKeyVersioner()

    versioner = Versioner(key_versioner, identify)

    config.registry.registerUtility(versioner)
    config.add_directive('get_versioner', get_versioner, action_wrap=False)
    config.add_request_method(get_versioner, 'versioner', reify=True)


def get_versioner(config_or_request):
    return config_or_request.registry.getUtility(IVersioner)


@implementer(IIdentityInspector)
class StrUnicodeIdentityInspector(object):

    def identify(self, str_or_unicode, ids_dict=None):
        if ids_dict is None:
            return str_or_unicode

        ids = ':'.join(['%s=%s' % (k, v) for (k, v) in ids_dict.iteritems()])

        return '%s:%s' % (str_or_unicode, ids)


@implementer(IIdentityInspector)
class TupleIdentityInspector(object):

    def __init__(self, identify):
        self._identify = identify

    def identify(self, tuple, ids_dict=None):
        return self._identify(tuple[0], tuple[1])


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

    def get_key(self, obj_or_cls):
        identity = self.identify(obj_or_cls)
        return '%s:v=%s' % (identity, self.key_versioner.get(identity))

    def get_multi_keys(self, objects_or_classes):
        keys = [self.identify(obj_or_cls)
                for obj_or_cls in objects_or_classes]

        versions = self.key_versioner.get_multi(keys)

        return ['%s:v=%s' % (key, version)
                for (key, version) in zip(keys, versions)]

    def incr(self, obj_or_cls, start=0):
        self.key_versioner.incr(self.identify(obj_or_cls))

        if not inspect.isclass(obj_or_cls):  # increment model class version
            identity = self.identify(obj_or_cls.__class__)
            self.key_versioner.incr(identity)
