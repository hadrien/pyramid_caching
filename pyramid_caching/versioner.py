import logging

from zope.interface import implementer

from pyramid_caching.interfaces import (
    IIdentityInspector,
    IVersioner,
    )

log = logging.getLogger(__name__)


def includeme(config):
    registry = config.registry

    def identify(model_obj_or_cls):
        y = registry.queryAdapter(model_obj_or_cls, IIdentityInspector)
        if y is None:
            raise TypeError(
                'Could not adapt %r to a cache identity' % model_obj_or_cls)
        return y

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

    config.add_directive('get_versioner', get_versioner, action_wrap=False)
    config.add_request_method(get_versioner, 'versioner', reify=True)

    def register():
        key_versioner = config.get_key_version_client()
        versioner = Versioner(key_versioner, config)
        config.registry.registerUtility(versioner)
        log.debug('registering versioner %r', versioner)

    config.action((__name__, 'versioner'), register, order=1)


def get_versioner(config_or_request):
    return config_or_request.registry.getUtility(IVersioner)


@implementer(IIdentityInspector)
class TupleIdentityInspector(object):
    def __init__(self, identify):
        self._identify = identify

    def identify(self, t):
        return ':'.join([self._identify(elem) for elem in t])


@implementer(IIdentityInspector)
class DictIdentityInspector(object):

    def __init__(self, identify):
        self._identify = identify

    def identify(self, dict_like):
        elems = ['%s=%s' % (self._identify(k), self._identify(v))
                 for k, v in sorted(dict_like.iteritems())]
        return ':'.join(elems)


@implementer(IVersioner)
class Versioner(object):

    def __init__(self, key_versioner, config, identify=None):
        self.key_versioner = key_versioner
        if identify is not None:
            self.identify = identify
        else:
            self.registry = config.registry

    def identify(self, x):
        y = self.registry.queryAdapter(x, IIdentityInspector)
        if y is None:
            raise TypeError('Could not adapt %r to a cache identity' % x)
        return y

    def get_multi_keys(self, things):
        keys = [self.identify(anything) for anything in things]

        versiontuples = self.key_versioner.get_multi(keys)

        return ['%s:v=%s' % (key, version) for (key, version) in versiontuples]

    def incr(self, obj_or_cls):
        self.key_versioner.incr(self.identify(obj_or_cls))
