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



class AuthenticationError(Exception): pass


#------------------------------------------------------------------------
# Demo Data Model

DANGER_STR = '&D\\anger\'"+<b>@?!mb'

class DemoData(object):
    """
    This is the basic data model of the MATA test server.

    It uses a deterministic random algorithm to simulate daily record. Each day
    it returns a varible number of devices id. Note that the data model only
    cover the basics. The view function fill in other data values using simple
    rules.
    """

    ACCOUNTS = {
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

    def __init__(self, username, password):
        if not (username in self.ACCOUNTS and self.ACCOUNTS[username]['password'] == password):
            raise AuthenticationError()
        self.account = self.ACCOUNTS[username]

    @classmethod
    def get_users(cls):
        return cls.ACCOUNTS.keys()


    def get_app_ids(self):
        return self.account['app_ids']


    def get_app(self, id):
        return self.APPLICATIONS.get(id)


    def get_install_device_id(self, date, app_id):
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


    @staticmethod
    def _get_campaign_name(app_name, campaign_id):
        return "%s campaign %s" % (app_name, campaign_id)




#------------------------------------------------------------------------


def requires_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        try:
            if not auth:
                raise AuthenticationError()
            account = DemoData(auth.username, auth.password)
            return f(account, *args, **kwargs)

        except AuthenticationError:
            return Response(
                        'Could not verify your access level for that URL.\nYou have to login with proper credentials',
                        401,
                        {'WWW-Authenticate': 'Basic realm="Login Required"'}
                        )
    return decorated


def _parse_date(s):
    assert (len(s) == 10) and (s[4] == s[7] == '-'), "Invalid date"
    return datetime.date(int(s[:4]), int(s[5:7]), int(s[8:10]))


def _json_response(data, **kwargs):
    return Response(json.dumps(data), mimetype='application/json', **kwargs)


def _bad_request_response(error_msgs):
    if isinstance(error_msgs, basestring):
        error_msgs = [error_msgs]
    return _json_response({'messages': error_msgs}, status=400)


def _unsupport_timezone_response(tz):
    return _bad_request_response([
                'Unsupported timezone: %s' % tz,
                'Supported timezones are: UTC'
            ])


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
        usernames = ', '.join(sorted(DemoData.get_users())),
        current_user = current_user,
        deauthorzie_url = deauthorzie_url,
        agg_url = agg_url,
        install_url = install_url,
    )



#------------------------------------------------------------------------

@app.route('/v1/application_list')
@requires_auth
def get_application_list(account):
    """
    Handler of the Application List Endpoint
    """
    app_list = [account.get_app(id) for id in account.get_app_ids()]
    return _json_response({
        'status': 'full',
        'data': app_list,
    })



@app.route('/v1/campaign_aggregate')
@requires_auth
def get_campaign_aggregate(account):
    """
    Handler of the Campaign Aggregate Endpoint
    """

    try:
        start_day = _parse_date(request.args['start_day'])
        end_day   = _parse_date(request.args['end_day'  ])

        tz = request.args.get('tz', 'UTC').upper()
        if tz != 'UTC':
            return _unsupport_timezone_response(tz)

        app_id = request.args.get('app_id')
        app_list = [app_id] if app_id else account.get_app_ids()

    except Exception, e:
        return _bad_request_response(str(e))

    # generate data
    agg_data = []
    iday = start_day
    while iday <= end_day:
        campaign_id = 10
        for app_id in app_list :
            app_name = account.get_app(app_id)['application_name']
            date_str = iday.isoformat()
            install_device_ids = account.get_install_device_id(date_str, app_id)

            # simple multiple of installs
            num_installs = len(install_device_ids)
            num_impressions = num_installs*5
            num_clicks = num_installs*2
            spend = num_installs * 150

            agg_data.append({
                "day": date_str,
                "app_id": app_id,
                "campaign_id": campaign_id,
                "campaign_name": DemoData._get_campaign_name(app_name, campaign_id),
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
def get_installs(account):
    """
    Handler of the Installs Endpoint
    """

    try:
        day = _parse_date(request.args['day'])

        tz = request.args.get('tz', 'UTC').upper()
        if tz != 'UTC':
            return _unsupport_timezone_response(tz)

        app_id = request.args.get('app_id')
        app_list = [app_id] if app_id else account.get_app_ids()

    except Exception, e:
        return _bad_request_response(str(e))

    # generate data
    installs = []
    for app_id in app_list:
        app_name = account.get_app(app_id)['application_name']
        install_device_ids = account.get_install_device_id(day, app_id)
        campaign_id = 10
        for did in install_device_ids:
            installs.append({
                "device_ids": {"udid": did},
                "app_id": app_id,
                "campaign_id": campaign_id,
                "campaign_name": DemoData._get_campaign_name(app_name, campaign_id),
                "creative": "cats.jpg",
                "location": "BF",
            })

    return _json_response({
        "status": "partial",
        "data": {
            "day": day.isoformat(),
            "installs": installs
        }
    })



if __name__ == '__main__':
    app.run(host='0.0.0.0')
