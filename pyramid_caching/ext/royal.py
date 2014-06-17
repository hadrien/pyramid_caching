"""Extension to integrate pyramid_caching into pyramid_royal applications."""

from __future__ import absolute_import

from pyramid.view import view_config
from royal import Collection, Item, Root
from royal.views import CollectionView, delete, ItemView, not_allowed

from pyramid_caching.cache import (
    cache_factory,
    QueryStringKeyModifier,
    ResourceDependency,
    )


def includeme(config):  # pragma: no cover
    """Register cached views into a Pyramid configurator."""
    config.scan(__name__)


class CachedResourceMixin(object):

    """Mixin class for Royal resources that can invalidate their cache key."""

    def invalidate(self):
        """Invalidate the cache key for this resource."""
        dep = ResourceDependency()
        key = dep(self, self.root.request)
        self.root.request.versioner.incr(key)


class CachedCollection(Collection, CachedResourceMixin):

    """A resource that supports caching and contains cached items."""

    __composite__ = True


class CachedItem(Item, CachedResourceMixin):

    """A cached resource that may belong to a cached collection."""

    pass


class CachedViewMixin(object):

    """Mixin class for Royal views that automatically invalidate the cache."""

    def __init__(self, context, request):  # pragma: no cover
        self.context = context
        self.request = request

    @view_config(context=CachedCollection,
                 request_method='DELETE',
                 permission='delete',
                 renderer='royal')
    @view_config(context=CachedItem,
                 request_method='DELETE',
                 permission='delete',
                 renderer='royal')
    def cached_delete(self):
        """Delete the resource and invalidate the cache."""
        response = delete(self.context, self.request)
        self.context.invalidate()
        return response

    @view_config(context=CachedCollection,
                 renderer='royal')
    @view_config(context=CachedItem,
                 renderer='royal')
    @view_config(context=Root,
                 renderer='royal')
    def cached_not_allowed(self):
        """Operation method is not valid for this resource type."""
        return not_allowed(self.context, self.request)


class CachedCollectionView(CollectionView, CachedViewMixin):

    """Collection of resources that caches the list of items it possesses."""

    @view_config(context=CachedCollection,
                 request_method='GET',
                 permission='index',
                 decorator=cache_factory(
                     depends_on=[
                         ResourceDependency(),
                         ],
                     varies_on=[
                         QueryStringKeyModifier(),
                         ],
                     ))
    def cached_index(self):
        """Respond with the list of items in this collection."""
        return self.index()

    @view_config(context=CachedCollection,
                 request_method='POST',
                 permission='create')
    def cached_create(self):
        """Add a new item to this collection and invalidate its cache."""
        response = self.create()
        self.context.invalidate()
        return response


class CachedItemView(ItemView, CachedViewMixin):

    """A resource that caches its representation."""

    @view_config(context=CachedItem,
                 request_method='GET',
                 permission='show',
                 decorator=cache_factory(
                     depends_on=[
                         ResourceDependency(),
                         ],
                     varies_on=[
                         QueryStringKeyModifier(),
                         ],
                     ))
    @view_config(context=Root,
                 request_method='GET',
                 permission='show',
                 decorator=cache_factory(
                     depends_on=[
                         ResourceDependency(),
                         ],
                     varies_on=[
                         QueryStringKeyModifier(),
                         ],
                     ))
    def cached_show(self):
        """Respond with a representation of this resource."""
        return self.show()

    @view_config(context=CachedItem,
                 request_method='PUT',
                 permission='replace')
    def cached_put(self):
        """Replace the current resource and invalidate its cache."""
        response = self.put()
        self.context.invalidate()
        return response

    @view_config(context=CachedItem,
                 request_method='PATCH',
                 permission='update')
    def cached_update(self):
        """Modify the resource and invalidate its cache."""
        response = self.patch()
        self.context.invalidate()
        return response

    @view_config(context=CachedItem,
                 request_method='POST')
    def cached_post(self):
        # Raises MethodNotAllowed
        self.post()
