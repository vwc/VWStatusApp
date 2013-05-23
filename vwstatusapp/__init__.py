from pyramid.config import Configurator
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy

from sqlalchemy import engine_from_config

from vwstatusapp.models import initialize_sql


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    initialize_sql(engine)
    authentication_policy = AuthTktAuthenticationPolicy('vwc1sa13')
    authorization_policy = ACLAuthorizationPolicy()
    config = Configurator(root_factory='vwstatusapp.models.RootFactory',
                          authentication_policy=authentication_policy,
                          authorization_policy=authorization_policy,
                          settings=settings)
    config.include('pyramid_persona')
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('status', '/status')
    config.add_route('quo', '/quo')
    config.add_route('signin', '/signin')
    config.add_route('join', '/join')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('users', '/{userid}')
    config.scan()
    return config.make_wsgi_app()
