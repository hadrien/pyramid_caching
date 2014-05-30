from __future__ import absolute_import

import os
import time

from redis import StrictRedis, RedisError

from pyramid_caching.exc import (
    CacheAddError,
    CacheGetError,
    CacheKeyAlreadyExists,
    VersionGetError,
    VersionIncrementError,
    VersionMasterVersionError,
    CacheDisabled,
)


def includeme(config):
    if not config.registry.settings['caching.enabled']:
        return
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
        """Create a cache entry. Raise CacheKeyAlreadyExists is this entry
        already exists.

        Note: Redis will only LRU evince volatile keys. (Default: 7 days)
        """
        if expiration is None:
            expiration = self.default_expiration

        try:
            rvalue = self.client.set(key, value, ex=expiration, nx=True)
        except RedisError as error:
            raise CacheAddError(error)

        if rvalue is None:
            raise CacheKeyAlreadyExists(key)

    def get(self, key):
        try:
            return self.client.get(key)
        except RedisError as error:
            raise CacheGetError(error)

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

    Notes about the Consistency and master-version:

    To ensure cache data consistency the model versioning must be consistent,
    thus a single failed model version increment would result in stale cache.

    To achieve consistent model versioning we must protect against two
    situations:

    - Glitch / temporary unavailability

    The model version increment operation raises VersionIncrementError
    exception is raised. In this case the write operation must be rollback.

    - Permanent loss of the version-store (and recovery with an empty one)

    The master-version is used together with dependency versions. If missing,
    this master-version is initialized to a new value. When a new empty
    version-store is reacheable, the master-version ends up being different
    than the previous one, hence effectively invalidating the whole cache.

    Note: the special master-version 'off' will inhibit caching while still
    maintaining the model versions.
    """

    MASTER_VERSION_KEY = 'cache'
    MASTER_VERSION_DISABLE_VALUE = 'off'

    def __init__(self, client):
        self.client = client

    def _get_master_version(self):
        """Return the master-version or None if the key is missing"""
        return self.client.get(self.MASTER_VERSION_KEY)

    def _generate_master_version(self):
        return int(time.time())

    def _set_master_version(self):
        """The set operation will silently fail if the key already exists.
        Thus we don't know what is the value of the stored master-version"""

        self.client.set(self.MASTER_VERSION_KEY,
                        self._generate_master_version(),
                        nx=True)

    def _handle_master_version(self, versions):
        if versions[0] is None:
            try:
                self._set_master_version()
                versions[0] = self._get_master_version()
            except RedisError as error:
                raise VersionMasterVersionError(error)

        if versions[0] is None:
            raise VersionMasterVersionError(
                "Still no master version after reset attempt")

        if versions[0] == self.MASTER_VERSION_DISABLE_VALUE:
            raise CacheDisabled('Disabled by master_version')

    def get_multi(self, keys):
        """Return an ordered list of tuple (key, value). The value default to 0
        """
        keys_with_master = [self.MASTER_VERSION_KEY] + keys

        try:
            versions = self.client.mget(keys_with_master)
        except RedisError as error:
            raise VersionGetError(error)

        self._handle_master_version(versions)

        versions = [v if v is not None else '0' for v in versions]

        return zip(keys_with_master, versions)

    def incr(self, key):
        """Increment a version. If the key was missing, the new value is 1"""
        try:
            self.client.incr(key)
        except RedisError as error:
            raise VersionIncrementError(error)

    def flush_all(self):
        self.client.flushall()
