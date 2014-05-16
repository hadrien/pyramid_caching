from __future__ import absolute_import

import os

import umemcache


def includeme(config):
    client = umemcache.Client(os.environ['MEMCACHE_URI'])

    client.connect()

    config.add_cache_client(client)


class UmemcacheWrapper(object):

    def __init__(self, client):
        self.client = client

    def get(self, key):
        value = self.client.get(key)
        if isinstance(value, tuple):
            return value[0]
        return value
