from __future__ import absolute_import

import os

import umemcache


def includeme(config):
    client = umemcache.Client(os.environ['MEMCACHE_URI'])

    client.connect()

    config.add_cache_client(UMemcacheWrapper(client))


class UMemcacheWrapper(object):

    def __init__(self, client):
        self.client = client

    def add(self, key, value):
        return self.client.add(key, value)

    def get(self, key):
        value = self.client.get(key)
        if isinstance(value, tuple):
            return value[0]
        return value

    def flush_all(self):
        self.client.flush_all()
