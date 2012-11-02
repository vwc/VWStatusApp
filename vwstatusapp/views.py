from datetime import datetime
from datetime import timedelta

from pyramid.httpexceptions import HTTPFound
from pyramid.security import authenticated_userid
from pyramid.security import remember
from pyramid.security import forget

from pyramid.view import view_config
from pyramid.view import forbidden_view_config


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
    if userid:
        users.append(user.id)
    signals = dbsession.query(Signal)
    results = []
    for k in range(8):
        start = datetime.now() - timedelta(k)
        end = datetime.now() - timedelta(k - 1)
        items = dbsession.query(Signal).filter(
            Signal.timestamp >= start, Signal.timestamp <= end)
        if len(items.all()) > 0:
            sigs = items.all()
            for sig in sigs:
                item = {}
                item['date'] = start
                item['signal'] = sig.signal
                item['timestamp'] = sig.timestamp
        else:
            item = {}
            item['date'] = start
            item['signal'] = 'All systems go!'
            item['timestamp'] = start
        results.append(item)
    ordered_signals = signals.order_by(Signal.timestamp.desc()).limit(30)
    return {'app_url': request.application_url,
            'static_url': request.static_url,
            'userid': userid,
            'user': user,
            'elapsed': get_elapsed,
            'user_chirps': False,
            'signals': ordered_signals.all(),
            'results': results}


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
             permission='edit',
             renderer='templates/status.pt')
def status_post(request):
    dbsession = DBSession()
    userid = authenticated_userid(request)
    user = dbsession.query(User).filter_by(userid=userid).one()
    chirp = request.params.get('chirp')
    author = user
    timestamp = datetime.now()
    new_chirp = Signal(chirp, author, timestamp)
    dbsession.add(new_chirp)
    return HTTPFound(location='/status')


@view_config(route_name='signin',
             permission='view',
             renderer='templates/signin.pt')
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
                'message': "The password is too short. Minimum 6 characters.",
                'userid': userid,
                'fullname': fullname,
                'about': about}
    user = User(userid, password, fullname, about)
    dbsession.add(user)
    headers = remember(request, userid)
    return HTTPFound(location='/',
                     headers=headers)
