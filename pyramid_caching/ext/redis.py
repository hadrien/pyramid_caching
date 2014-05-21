from __future__ import absolute_import

import os

from redis import StrictRedis

from pyramid_caching.exc import (CacheError, CacheKeyAlreadyExists)

def includeme(config):
    include_cache_store(config)
    include_version_store(config)

def include_cache_store(config):
    uri = os.environ['CACHE_STORE_REDIS_URI']
    client = StrictRedis.from_url(uri)
    config.add_cache_client(RedisCacheWrapper(client))

def include_version_store(config):
    uri = os.environ['VERSION_STORE_REDIS_URI']
    client = StrictRedis.from_url(uri)
    config.add_key_version_client(RedisVersionWrapper(client))


class RedisCacheWrapper(object):

    def __init__(self, client):
        self.default_expiration = 3600 * 24 * 7  # 7 days
        self.client = client

    def add(self, key, value, expiration=None):
        """
        Note: Redis will only LRU evince volatile keys.

        Default expiration: 7 days
        """
        if expiration is None:
            expiration = self.default_expiration

        rvalue = self.client.set(key, value, ex=expiration, nx=True)
        if rvalue is None:
            raise CacheKeyAlreadyExists(key)

    def get(self, key):
        return self.client.get(key)

    def flush_all(self):
        self.client.flushall()


class RedisVersionWrapper(object):
    """Redis implementation of the IKeyVersioner interface.

    This KeyVersioner use Redis ability to namespace content with seperate
    db, thus not prefixing the keys with anything like 'version:'.

    The default value for this implementation is 0 since the INCR operation
    enforce a value of 1 after executing on a non-existing key.
    See `Redis documentation for INCR <http://redis.io/commands/incr>`_

    Note: the return value are always string type.
    """

    def __init__(self, client):
        self.client = client

    def get(self, key):
        value = self.client.get(key)
        return value if value is not None else '0'

    def get_multi(self, keys):
        return [v if v is not None else '0'
                for v in self.client.mget(keys)]

    def incr(self, key):
        self.client.incr(key)

    def flush_all(self):
        self.client.flushall()
