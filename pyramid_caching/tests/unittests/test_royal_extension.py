import unittest

import mock


class RoyalExtensionCachedCollectionViewTests(unittest.TestCase):
    @mock.patch('royal.views.CollectionView.index')
    def test_calls_index(self, m_index):
        from pyramid_caching.ext.royal import CachedCollectionView
        ccv = CachedCollectionView(None, None)
        response = ccv.cached_index()
        m_index.assert_called_once_with()
        self.assertEqual(m_index.return_value, response)

    @mock.patch('royal.views.CollectionView.create')
    def test_calls_create(self, m_create):
        from pyramid_caching.ext.royal import CachedCollectionView
        ccv = CachedCollectionView(mock.Mock(), None)
        response = ccv.cached_create()
        m_create.assert_called_once_with()
        self.assertEqual(m_create.return_value, response)

    @mock.patch('royal.views.CollectionView.create')
    def test_create_invalidates_context(self, m_create):
        from pyramid_caching.ext.royal import CachedCollectionView
        context = mock.Mock()
        ccv = CachedCollectionView(context, None)
        ccv.cached_create()
        context.invalidate.assert_called_once_with()

    @mock.patch('pyramid_caching.ext.royal.delete')
    def test_calls_delete(self, m_delete):
        from pyramid_caching.ext.royal import CachedCollectionView
        ccv = CachedCollectionView(mock.Mock(), None)
        response = ccv.cached_delete()
        m_delete.assert_called_once_with(ccv.context, ccv.request)
        self.assertEqual(m_delete.return_value, response)

    @mock.patch('pyramid_caching.ext.royal.delete')
    def test_delete_invalidates_context(self, m_delete):
        from pyramid_caching.ext.royal import CachedCollectionView
        context = mock.Mock()
        ccv = CachedCollectionView(context, None)
        ccv.cached_delete()
        context.invalidate.assert_called_once_with()

    @mock.patch('pyramid_caching.ext.royal.not_allowed')
    def test_calls_not_allowed(self, m_not_allowed):
        from pyramid_caching.ext.royal import CachedCollectionView
        context = mock.Mock()
        ccv = CachedCollectionView(context, None)
        response = ccv.cached_not_allowed()
        m_not_allowed.assert_called_once_with(ccv.context, ccv.request)
        self.assertEqual(m_not_allowed.return_value, response)


class RoyalExtensionCachedItemViewTests(unittest.TestCase):
    @mock.patch('royal.views.ItemView.show')
    def test_cached_item_calls_show(self, m_show):
        from pyramid_caching.ext.royal import CachedItemView
        civ = CachedItemView(None, None)
        response = civ.cached_show()
        m_show.assert_called_once_with()
        self.assertEqual(m_show.return_value, response)

    @mock.patch('royal.views.ItemView.put')
    def test_cached_item_calls_put(self, m_put):
        from pyramid_caching.ext.royal import CachedItemView
        civ = CachedItemView(mock.Mock(), None)
        response = civ.cached_put()
        m_put.assert_called_once_with()
        self.assertEqual(m_put.return_value, response)

    @mock.patch('royal.views.ItemView.put')
    def test_cached_item_put_invalidates_context(self, m_put):
        from pyramid_caching.ext.royal import CachedItemView
        context = mock.Mock()
        civ = CachedItemView(context, None)
        civ.cached_put()
        context.invalidate.assert_called_once_with()

    @mock.patch('royal.views.ItemView.patch')
    def test_cached_item_calls_update(self, m_patch):
        from pyramid_caching.ext.royal import CachedItemView
        civ = CachedItemView(mock.Mock(), None)
        response = civ.cached_update()
        m_patch.assert_called_once_with()
        self.assertEqual(m_patch.return_value, response)

    @mock.patch('royal.views.ItemView.patch')
    def test_cached_item_update_invalidates_context(self, m_patch):
        from pyramid_caching.ext.royal import CachedItemView
        context = mock.Mock()
        civ = CachedItemView(context, None)
        civ.cached_update()
        context.invalidate.assert_called_once_with()

    @mock.patch('royal.views.ItemView.post')
    def test_cached_item_calls_post(self, m_post):
        from pyramid_caching.ext.royal import CachedItemView
        civ = CachedItemView(mock.Mock(), None)
        civ.cached_post()
        m_post.assert_called_once_with()

    @mock.patch('pyramid_caching.ext.royal.delete')
    def test_cached_item_calls_delete(self, m_delete):
        from pyramid_caching.ext.royal import CachedItemView
        civ = CachedItemView(mock.Mock(), None)
        response = civ.cached_delete()
        m_delete.assert_called_once_with(civ.context, civ.request)
        self.assertEqual(m_delete.return_value, response)

    @mock.patch('pyramid_caching.ext.royal.delete')
    def test_cached_item_delete_invalidates_context(self, m_delete):
        from pyramid_caching.ext.royal import CachedItemView
        context = mock.Mock()
        civ = CachedItemView(context, None)
        civ.cached_delete()
        context.invalidate.assert_called_once_with()

    @mock.patch('pyramid_caching.ext.royal.not_allowed')
    def test_cached_item_calls_not_allowed(self, m_not_allowed):
        from pyramid_caching.ext.royal import CachedItemView
        context = mock.Mock()
        civ = CachedItemView(context, None)
        response = civ.cached_not_allowed()
        m_not_allowed.assert_called_once_with(civ.context, civ.request)
        self.assertEqual(m_not_allowed.return_value, response)


class RoyalExtensionCachedResourceTests(unittest.TestCase):
    def test_invalidate_collection_key(self):
        from pyramid_caching.ext.royal import CachedCollection, Root
        request = mock.Mock()
        root = Root(request)
        resource = CachedCollection('myname', root)
        resource.invalidate()
        request.versioner.incr.assert_called_once_with(('myname',))

    def test_invalidate_item_key(self):
        from pyramid_caching.ext.royal import CachedCollection, Root
        request = mock.Mock()
        root = Root(request)
        coll = CachedCollection('mycoll', root)
        resource = CachedCollection('myitem', coll)
        resource.invalidate()
        request.versioner.incr.assert_called_once_with(
            ('myitem', {'mycoll': 'myitem'}))
