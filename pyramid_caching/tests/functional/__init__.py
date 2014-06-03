import os
import unittest

import webtest

from pyramid.config import Configurator
from pyramid.decorator import reify


def setupPackage():
    os.environ['CACHE_STORE_REDIS_URI'] = 'redis://127.0.0.1:6379/5'
    os.environ['VERSION_STORE_REDIS_URI'] = 'redis://127.0.0.1:6379/8'


def tearDownPackage():
    os.environ.pop('CACHE_STORE_REDIS_URI', None)
    os.environ.pop('VERSION_STORE_REDIS_URI', None)


class Base(unittest.TestCase):

    maxDiff = None

    @reify
    def config(self):
        _config = Configurator(settings={
            'sqlalchemy.url': 'sqlite:///:memory:',
            })
        _config.include('example')
        self.addCleanup(delattr, self, 'config')

        def flush_cache():
            _config.get_cache_client().flush_all()

        if hasattr(_config, 'get_cache_client'):
            self.addCleanup(flush_cache)
        return _config

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
    def key_versioner_client(self):
        return self.config.get_key_version_client()

    @property
    def cache_client(self):
        return self.config.get_cache_client()

    @property
    def cache_manager(self):
        return self.config.get_cache_manager()
