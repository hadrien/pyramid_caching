from zope.interface import Interface, Attribute


class IKeyVersioner(Interface):

    def get(key, default=0):
        """Get a key's version.

        If found, key's version is returned, else ``default``.
        """

    def get_multi(keys, default=0):
        """Get versions for a list of keys.

        If found, a dict containing keys with their corresponding versions
        is returned, else the keys versions are initialized to ``default``
        i.e., {'key': 0, ...}.

        Prefix 'ver_' is added to each input key for Memcache
        query, however prefix is removed before returning results.
        """

    def incr(key, start=0):
        """Increment an existing key version or add a new version starting at
        ``start``.
        """


class IVersioner(Interface):

    def get_key(obj_or_cls):
        ""

    def get_multi_keys(objects_or_classes):
        """Returns all versioned keys of each class or object in
        classes_or_objects.

        .. code-block:: ipython

            >>> from pyramid_caching.versioners import Versioner
            >>> from myapp.model import MyModel
            >>> versioner = Versioner()
            >>> res = versioner.get_class_keys([MyModel])
            >>> res == ['myapp.model.MyModel.v_0']

        """

    def incr(obj_or_cls, start=0):
        "Increment version of object and class or of class only"


class IIdentityInspector(Interface):

    def identify(obj_or_cls):
        """Return a string that can be used to uniquely identify ``obj_or_cls``
        :param obj_or_cls: object or class to identify
        """


class ICacheClient(Interface):

    def add(key, obj):
        pass

    def get(key):
        pass

    def get_multi(keys):
        pass

    def incr(key):
        pass


class ICacheManager(Interface):
    pass


class ISerializer(Interface):

    name = Attribute('unique name registered for the serializer')

    def serialize(obj):
        pass

    def deserialize(data):
        pass
