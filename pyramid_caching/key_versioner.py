import logging

from zope.interface import classImplements

from pyramid_caching.interfaces import IKeyVersioner

log = logging.getLogger(__name__)


def includeme(config):
    config.add_directive('get_key_version_client', get_key_version_client,
                         action_wrap=False)
    config.add_directive('add_key_version_client', add_key_version_client)


def get_key_version_client(config_or_request):
    return config_or_request.registry.getUtility(IKeyVersioner)


def add_key_version_client(config, key_versioner):
    if not IKeyVersioner.implementedBy(key_versioner.__class__):
        log.debug('assuming %r implements %r',
                  key_versioner.__class__, IKeyVersioner)
        classImplements(key_versioner.__class__, IKeyVersioner)

    def register():
        log.debug('registering KeyVersioner %r', key_versioner)
        config.registry.registerUtility(key_versioner, IKeyVersioner)

    config.action((__name__, 'key_version_client'), register, order=0)
