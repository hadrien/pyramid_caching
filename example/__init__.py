

def includeme(config):  # pragma no cover
    config.include('pyramid_caching')
    config.include('pyramid_caching.ext.umemcache')
    config.include('.model')
    config.include('.views')
