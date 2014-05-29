from zope.interface import Interface, Attribute


class IKeyVersioner(Interface):
    """
    Notes about the default values:

    There is two default values :
    - the return value of get()/get_multi() when the version doesn't exist
    - the stored version after an incr() operation

    Those default values are implementation specific and MUST be equivalent.

    See Redis implementation.
    """

    def get_multi(keys):
        """Get versions for a list of keys.

        Return a list of corresponding versions. Defaults is implementation
        specific.
        """

    def incr(key):
        """Increment an existing key version. Defaults is implementation
        specific.
        """


class IVersioner(Interface):

    def get_multi_keys(objects_or_classes):
        """Returns all versioned keys of each class or object in
        classes_or_objects.

        .. code-block:: ipython

            >>> from pyramid_caching.versioner import Versioner
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


class ICacheManager(Interface):
    pass


class ISerializer(Interface):
    def dumps(obj):
        """Return a flat binary representation of the object."""

    def loads(data):
        """Returns an instance of the object stored in the binary data."""


class ISerializationAdapter(Interface):

    name = Attribute('unique name registered for the serializer')

    def serialize(obj):
        pass

    def deserialize(data):
        pass


class ICacheHit(Interface):
    cache_key = Attribute("The cache key object")
    request = Attribute("The request object")


class ICacheMiss(Interface):
    cache_key = Attribute("The cache key object")
    request = Attribute("The request object")
