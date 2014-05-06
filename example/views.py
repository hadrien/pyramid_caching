from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound

from pyramid_caching.cache import cache_basic, cache_factory

from example.model import User


def includeme(config):
    config.add_route(name='user', pattern='/users/{user_id}')
    config.scan(__name__)


@view_config(
    route_name='user',
    renderer='json',
    request_method='GET',
    decorator=cache_factory(depends_on=({User: {'matchdict': ['user_id']}})),
    )
def get_user(request):
    user = User.get(request.matchdict['user_id'])
    if user is None:
        raise HTTPNotFound()
    return {
        'id': user.id,
        'name': user.name,
    }


@cache_basic()
def fibonacci(n):
    if n == 0:
        return 0
    if n == 1:
        return 1

    return fibonacci(n - 1) + fibonacci(n - 2)
