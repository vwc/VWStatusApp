from datetime import datetime

from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPNotFound
from pyramid.security import authenticated_userid
from pyramid.security import remember
from pyramid.security import forget
from pyramid.url import route_url

from pyramid.response import Response
from pyramid.view import view_config


from vwstatusapp.models import DBSession
from vwstatusapp.models import User
from vwstatusapp.models import Signal
from vwstatusapp.models import check_login

from repoze.timeago import get_elapsed


@view_config(route_name='home',
                permission='view',
                renderer='templates/main.pt')
def signals_view(request):
    dbsession = DBSession()
    userid = authenticated_userid(request)
    user = dbsession.query(User).filter_by(userid=userid).first()
    users = []
    users.append(user.id)
    signals = dbsession.query(Signal).filter(Signal.author_id.in_(users))
    ordered_signals = signals.order_by(Signal.timestamp.desc()).limit(30)
    return {'app_url': request.application_url,
            'static_url': request.static_url,
            'userid': userid,
            'user': user,
            'elapsed': get_elapsed,
            'user_chirps': False,
            'signals': ordered_signals.all()}


@view_config(route_name='status',
                permission='view',
                renderer='templates/status.pt')
def status_view(request):
    dbsession = DBSession()
    userid = authenticated_userid(request)
    user = dbsession.query(User).filter_by(userid=userid).first()
    signals = dbsession.query(Signal).filter(Signal.author_id == userid)
    signals = signals.order_by(Signal.timestamp.desc()).limit(30)
    return {'app_url': request.application_url,
            'static_url': request.static_url,
            'userid': userid,
            'user': user,
            'elapsed': get_elapsed,
            'user_chirps': False,
            'signals': signals.all()}


@view_config(route_name='status',
                request_method='POST',
                permission='view',
                renderer='templates/status.pt')
def status_post(request):
    dbsession = DBSession()
    userid = authenticated_userid(request)
    user = dbsession.query(User).filter_by(userid=userid).one()
    chirp = request.params.get('chirp')
    author = user
    timestamp = datetime.utcnow()
    new_chirp = Signal(chirp, author, timestamp)
    dbsession.add(new_chirp)
    return HTTPFound(location='/status')


@view_config(context='pyramid.httpexceptions.HTTPForbidden',
                request_method='GET',
                renderer='templates/login.pt')
def login_page(request):
    login = ''
    message = ''
    return {'app_url': request.application_url,
            'static_url': request.static_url,
            'message': message,
            'login': login}


@view_config(context='pyramid.httpexceptions.HTTPForbidden',
                request_method='POST',
                renderer='templates/login.pt')
def login(request):
    login = request.params['login']
    password = request.params['password']
    if check_login(login, password):
        headers = remember(request, login)
        return HTTPFound(location='/',
                         headers=headers)
    message = 'Failed login'
    return {'app_url': request.application_url,
            'static_url': request.static_url,
            'message': message,
            'login': login}


@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    return HTTPFound(location='/',
                     headers=headers)


@view_config(route_name='join',
                request_method='GET',
                renderer='templates/join.pt')
def join_page(request):
    return {'app_url': request.application_url,
            'static_url': request.static_url,
            'message': '',
            'userid': '',
            'fullname': '',
            'about': ''}


@view_config(route_name='join',
                request_method='POST',
                renderer='templates/join.pt')
def join(request):
    dbsession = DBSession()
    userid = request.params.get('userid')
    user = dbsession.query(User).filter_by(userid=userid).first()
    password = request.params.get('password')
    confirm = request.params.get('confirm')
    fullname = request.params.get('fullname')
    about = request.params.get('about')
    if user:
        return {'app_url': request.application_url,
            'static_url': request.static_url,
            'message': "The userid %s already exists." % userid,
            'userid': userid,
            'fullname': fullname,
            'about': about}
    if confirm != password:
        return {'app_url': request.application_url,
            'static_url': request.static_url,
            'message': "The passwords don't match.",
            'userid': userid,
            'fullname': fullname,
            'about': about}
    if len(password) < 6:
        return {'app_url': request.application_url,
            'static_url': request.static_url,
            'message': "The password is too short. Minimum is 6 characters.",
            'userid': userid,
            'fullname': fullname,
            'about': about}
    user = User(userid, password, fullname, about)
    dbsession.add(user)
    headers = remember(request, userid)
    return HTTPFound(location='/',
                     headers=headers)
