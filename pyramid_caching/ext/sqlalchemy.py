"""Extension to perform cache invalidation in SQLAlchemy ORM classes."""

from __future__ import absolute_import

import functools
import logging
import weakref

from zope.interface import implementer

from pyramid_caching.exc import VersionIncrementError
from pyramid_caching.interfaces import IIdentityInspector

from sqlalchemy import event

log = logging.getLogger(__name__)


def register_sqlalchemy_caching(config, session_factory, base_cls,
                                identity_inspector=None):
    """Register SQLAlchemy session commit hooks for cache invalidation.

    If the `caching.enabled` configuration setting is set to `true`, no hooks
    will be registered.
    """
    if not config.registry.settings['caching.enabled']:
        return

    registry = config.registry

    if identity_inspector is None:
        identity_inspector = DefaultIdentityInspector()

    registry.registerAdapter(
        lambda x: identity_inspector.identify_collection(x),
        required=[Collection],
        provided=IIdentityInspector)
    registry.registerAdapter(
        lambda x: identity_inspector.identify_instance(x),
        required=[base_cls],
        provided=IIdentityInspector)
    registry.registerAdapter(
        lambda x: identity_inspector.identify_class(x),
        required=[base_cls.__class__],
        provided=IIdentityInspector)

    config.action((__name__, 'session_caching_hook'),
                  _register_sqla_session_caching_hook,
                  args=(config, session_factory),
                  order=3)


def includeme(config):
    """Add a Pyramid configuration method to register session hooks."""
    config.add_directive('register_sqlalchemy_caching',
                         register_sqlalchemy_caching)


class Collection(object):

    """Annotates an instance object to refer to the containing entity."""

    def __init__(self, instance):
        """Identify this model instance as a collection."""
        self.instance = weakref.ref(instance)


def _register_sqla_session_caching_hook(config, session_factory):
    def identify(entity):
        registry = config.registry
        y = registry.queryAdapter(entity, IIdentityInspector)
        if y is None:
            raise TypeError("Could not adapt %r" % entity)
        return y

    def on_before_commit(session):
        versioner = config.get_versioner()
        cache_keys = _get_modified_entity_keys(session, identify)
        after_commit = functools.partial(
            _increment_versions_after_commit, versioner, cache_keys)
        event.listen(session, 'after_commit', after_commit)

    event.listen(session_factory, 'before_commit', on_before_commit)


def _get_modified_entity_keys(session, identify_func):
        identities = set()
        for entity in session.new:
            identities.add(identify_func(Collection(entity)))
        for entity in session.dirty:
            identities.add(identify_func(Collection(entity)))
            identities.add(identify_func(entity))
        for entity in session.deleted:
            identities.add(identify_func(Collection(entity)))
            identities.add(identify_func(entity))
        return identities


def _increment_versions_after_commit(versioner, cache_keys, *args):
    for key in cache_keys:
        if not key:
            continue
        try:
            versioner.incr(key)
        except VersionIncrementError:
            log.exception("Entity version increment failed key=%s", key)


@implementer(IIdentityInspector)
class DefaultIdentityInspector(object):

    """Generate a cache key from SQLAlchemy ORM classes."""

    def table_name(self, entity):
        """The name of the base table of an ORM entity."""
        return entity.__tablename__

    def primary_key_column_names(self, instance):
        """The column names identifying the row of this instance."""
        table = instance.__table__
        return table.primary_key.columns.keys()

    def foreign_key_column_names(self, instance):
        """The column names that define relationships with this instance."""
        table = instance.__table__
        return [fk.parent.name for fk in table.foreign_keys]

    def _entity_cache_key(self, instance, column_names):
        ids = []
        for col_name in sorted(column_names):
            value = getattr(instance, col_name)
            if value is not None:
                ids.append('{}={}'.format(col_name, value))
            else:
                log.warning('Caching key %s:%s is None',
                            self.table_name(instance), col_name)
        return ':'.join([self.table_name(instance)] + ids)

    def identify_class(self, cls):
        """Get the cache key for the model class."""
        return self.table_name(cls)

    def identify_collection(self, collection):
        """Get the cache key for the collection containing a model instance.

        With a table user_message with a foreign key `user_id`, the collection
        containing the object `<UserMessage user_id=123, id=456>` will have the
        cache key: `'user_message:user_id=123'`.
        """
        instance = collection.instance()
        if instance is None:
            # Referent has been garbage collected.
            return ''
        column_names = self.foreign_key_column_names(instance)
        if column_names is None:
            return ''
        return self._entity_cache_key(instance, column_names)

    def identify_instance(self, instance):
        """Get the cache key for a model instance.

        With a table user_message with a composite primary key `user_id` and
        `id`, an object `<UserMessage user_id=123, id=456>` will have the cache
        key: `'user_message:id=456:user_id=123'`.
        """
        column_names = self.primary_key_column_names(instance)
        if column_names is None:
            return ''
        return self._entity_cache_key(instance, column_names)
