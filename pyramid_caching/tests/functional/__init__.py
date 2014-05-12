import unittest

import webtest

from pyramid.config import Configurator
from pyramid.decorator import reify


class Base(unittest.TestCase):

    maxDiff = None

    @reify
    def config(self):
        self.addCleanup(self.cleanup)
        _config = Configurator(settings={
            'sqlalchemy.url': 'sqlite:///:memory:',
            })
        _config.include('example')
        _config.commit()
        return _config

    def cleanup(self):
        from pyramid_caching.cache import UndecorateEvent
        self.config.registry.notify(UndecorateEvent())
        delattr(self, 'config')

    @reify
    def app(self):
        self.addCleanup(delattr, self, 'app')
        return webtest.TestApp(self.config.make_wsgi_app())

    @property
    def registry(self):  # pragma no cover
        return self.config.registry

    @property
    def versioner(self):
        return self.config.get_versioner()

    @property
    def cache_client(self):
        return self.config.get_cache_client()
