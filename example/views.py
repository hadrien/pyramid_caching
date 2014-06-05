from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound

from pyramid_caching.cache import (
    cache_factory,
    CollectionDependency,
    QueryStringPredicate,
    RouteDependency,
    )

from example.model import User


def includeme(config):
    config.add_route(name='user', pattern='/users/{user_id}')
    config.add_route(name='users', pattern='/users')
    config.scan(__name__)


@view_config(
    route_name='user',
    renderer='json',
    request_method='GET',
    decorator=cache_factory(depends_on=[
        RouteDependency(User, {'user_id': 'id'}),
        ]),
    )
def get_user(request):
    user = User.get(request.matchdict['user_id'])
    if user is None:
        raise HTTPNotFound()
    return {
        'id': user.id,
        'name': user.name,
        }


@view_config(
    route_name='users',
    renderer='json',
    request_method='GET',
    decorator=cache_factory(
        predicates=[
            QueryStringPredicate(['name']),
            ],
        depends_on=[
            CollectionDependency(User),
            ],
        ),
    )
def list_users(request):
    if 'name' in request.params:
        users = User.filter_by_name(request.params['name'])
    else:
        users = User.all()
    return [{
        'id': user.id,
        'name': user.name,
        }
        for user in users]
