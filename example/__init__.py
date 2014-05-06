

def includeme(config):
    config.include('pyramid_caching')
    config.include('.model')
    config.include('.views')
