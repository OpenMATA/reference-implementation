# MATA Test Server

import datetime
import functools
import hashlib
import urlparse

try:
    import json
except ImportError:
    import simplejson as json
from dateutil.parser import *
from flask import *

app = Flask(__name__)

app.debug = True


#TODO: clean this up

def generate_installs(date, app_id):
    """
    A deterministic algorithm to generate random data for a day
    """
    msg = 'some deterministic msg %s,%s' % (date,app_id)
    h = hashlib.md5(msg)
    # a random number in [0, 1)
    r0 = ord(h.digest()[0]) / 256.0

    num_installs = int(10 + 10*r0)

    device_id_list = []
    for i in xrange(num_installs):
        h.update('tada %s' % i)
        device_id_list.append(h.hexdigest())

    return device_id_list


#------------------------------------------------------------------------
# Demo Data Model

DANGER_STR = '&D\\anger\'"+<b>@?!mb'

ACCOUNT = {
'test1': dict(username='test1', password='test1', app_ids=['12341', '12342', DANGER_STR]),
'test2': dict(username='test2', password='test2', app_ids=['12351', '12352']),
}

APPLICATIONS = {
'12341'   : {"app_id": "12341",   "application_name": 'Best Game Ever',       "bundle_id": "com.demo.best_game"},
'12342'   : {"app_id": "12342",   "application_name": u'\u4e09\u570b\u5fd73', "bundle_id": "com.demo.three_kingdom3"},
DANGER_STR: {"app_id": DANGER_STR,"application_name": DANGER_STR ,            "bundle_id": "com.demo.danger"},
'12351'   : {"app_id": "12351",   "application_name": 'Test app2',            "bundle_id": "com.demo.test_app2"},
'12352'   : {"app_id": "12352",   "application_name": u'\u6c34\u6ef8\u50b3',  "bundle_id": "com.demo.water_margin"},
}


def _get_campaign_name(app_name, campaign_id):
    return "%s campaign %s" % (app_name, campaign_id)


def check_auth(username, password):
    return username in ACCOUNT and ACCOUNT[username]['password'] == password



#------------------------------------------------------------------------


def requires_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if auth and check_auth(auth.username, auth.password):
            return f(*args, **kwargs)
        return Response(
                    'Could not verify your access level for that URL.\nYou have to login with proper credentials',
                    401,
                    {'WWW-Authenticate': 'Basic realm="Login Required"'}
                    )
    return decorated


def _json_response(data, **kwargs):
    return Response(json.dumps(data), mimetype='application/json', **kwargs)


@app.route('/')
def index():

    try:
        # TODO: this may not work
        current_user = request.authorization.username
    except:
        current_user = 'N/A'

    # deauthorzie URL (verified works in Chrome)
    parts = list(urlparse.urlsplit(request.url))
    parts[1] = 'x:y@' + parts[1]
    deauthorzie_url = urlparse.urlunsplit(parts)

    today = datetime.datetime.utcnow().date().isoformat()

    agg_url = "/v1/campaign_aggregate?start_day=%s&end_day=%s" % (today, today)
    install_url = "/v1/installs?day=%s" % (today,)

    return render_template('index.html',
        usernames = ', '.join(sorted(ACCOUNT.keys())),
        current_user = current_user,
        deauthorzie_url = deauthorzie_url,
        agg_url = agg_url,
        install_url = install_url,
    )


def get_app_list(request):
    """
    Return get a list of apps for the authenticated user
    """
    app_ids = get_app_id_list(request)
    return [APPLICATIONS[id] for id in app_ids]


def get_app_id_list(request):
    """
    Return get a list of app_id for the authenticated user
    """
    username = request.authorization.username
    return ACCOUNT[username]['app_ids']


#------------------------------------------------------------------------

@app.route('/v1/application_list')
@requires_auth
def get_application_list():
    """
    Handler of the Application List Endpoint
    """
    app_list = get_app_list(request)
    return _json_response({
        'status': 'full',
        'data': app_list,
    })



@app.route('/v1/campaign_aggregate')
@requires_auth
def get_campaign_aggregate():
    """
    Handler of the Campaign Aggregate Endpoint
    """

    # read query parameters
    tz = request.args.get('tz', 'UTC')
    tz = tz.upper()
    if tz != 'UTC':
        return _json_response({
            'status': '400',
            'messages': [
                'Unsupported timezone: %s' % tz,
                'Supported timezones are: UTC'
            ]
        }, status=400)

    start_day = request.args['start_day']
    end_day   = request.args['end_day']
    start_day = parse(start_day)
    end_day   = parse(end_day)

    app_id = request.args.get('app_id')
    if app_id:
        app_list = [app_id]
    else:
        app_list = get_app_id_list(request)


    # generate data
    agg_data = []
    iday = start_day
    while iday <= end_day:
        campaign_id = 10
        for app_id in app_list :
            app_name = APPLICATIONS[app_id]['application_name']
            date_str = iday.date().isoformat()
            install_device_ids = generate_installs(date_str, app_id)

            num_installs = len(install_device_ids)
            num_impressions = int(num_installs*5)
            num_clicks = int(num_installs*2)
            spend = 150 * num_installs

            agg_data.append({
                "day": date_str,
                "app_id": app_id,
                "campaign_id": campaign_id,
                "campaign_name": _get_campaign_name(app_name, campaign_id),
                "impressions": num_impressions,
                "clicks": num_clicks,
                "downloads": num_installs,
                "spend": spend,
                "target_manufacturer": [
                    "Samsung",
                ],
                "target_platform": [
                    "Nexus S",
                    u"\u963f\u91cc\u4e91",
                ],
            })

        iday += datetime.timedelta(1)

    return _json_response({
        "status": "partial",
        "data": agg_data,
    })



@app.route('/v1/installs')
@requires_auth
def get_installs():
    """
    Handler of the Installs Endpoint
    """

    # read query parameters
    tz = request.args.get('tz', 'UTC')
    tz = tz.upper()
    if tz != 'UTC':
        return _json_response({
            'status': '400',
            'messages': [
                'Unsupported timezone: %s' % tz,
                'Supported timezones are: UTC'
            ]
        }, status=400)

    date = request.args['day']

    app_id = request.args.get('app_id')
    if app_id:
        app_list = [app_id]
    else:
        app_list = get_app_id_list(request)

    # generate data
    installs = []
    for app_id in app_list:
        app_name = APPLICATIONS[app_id]['application_name']
        install_device_ids = generate_installs(date, app_id)
        campaign_id = 10
        for did in install_device_ids:
            installs.append({
                "device_ids": {"udid": did},
                "app_id": app_id,
                "campaign_id": campaign_id,
                "campaign_name": _get_campaign_name(app_name, campaign_id),
                "creative": "cats.jpg",
                "location": "BF",
            })

    return _json_response({
        "status": "partial",
        "data": {
            "day": date,
            "installs": installs
        }
    })



if __name__ == '__main__':
    app.run(host='0.0.0.0')
