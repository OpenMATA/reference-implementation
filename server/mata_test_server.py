# MATA Test Server

import datetime
import functools
import hashlib
import itertools
import operator
import urlparse

try:
    import json
except ImportError:
    import simplejson as json
from flask import *

from sample_model import DemoData

app = Flask(__name__)
app.debug = True



#------------------------------------------------------------------------
# Helper functions

def requires_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        try:
            if not auth:
                raise DemoData.AuthenticationError()
            account = DemoData(auth.username, auth.password)
            return f(account, *args, **kwargs)

        except DemoData.AuthenticationError:
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



#------------------------------------------------------------------------
# View functions

@app.route('/')
def index():
    try:
        # TODO: this may not work
        current_user = request.authorization.username
    except:
        current_user = 'N/A'

    # deauthorzie URL (Link works in Firefox and Chrome. In Opera need to paste in address bar. Not work in IE.)
    parts = list(urlparse.urlsplit(request.url))
    parts[1] = 'foobar@' + parts[1]
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



@app.route('/v1/application_list')
@requires_auth
def get_application_list(account):
    """
    Handler of the Application List Endpoint
    """
    app_list = [account.get_app(id) for id in account.get_app_ids()]
    # assume DemoData.APPLICATIONS' match MATA's response
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
        for app_id in app_list:
            app = account.get_app(app_id)
            if not app:
                continue

            # construct some attributes
            app_name = app['application_name']
            date_str = iday.isoformat()
            installs = account.generate_install_data(date_str, app_id)

            def _gen_campaign(num_installs, campaign_id, cost):
                # simple multiple of installs
                num_impressions = num_installs*5
                num_clicks = num_installs*2

                agg_data.append({
                    "day"                 : date_str,
                    "app_id"              : app_id,
                    "bundle_id"           : app['bundle_id'],
                    "campaign_id"         : campaign_id,
                    "campaign_name"       : DemoData._get_campaign_name(app_name, campaign_id),
                    "impressions"         : num_impressions,
                    "clicks"              : num_clicks,
                    "downloads"           : num_installs,
                    "spend"               : cost,
                    "currency"            : "USD",
                    "target_manufacturer" : ["Samsung"],
                    "target_platform"     : ["Nexus S", u"\u963f\u91cc\u4e91"],
                    "target_country_code" : ["US"],
                })

            get_campaign_id = operator.itemgetter(1)
            installs.sort(key=get_campaign_id)
            for campaign_id, _installs_grouped in itertools.groupby(installs, get_campaign_id):
                _installs_grouped = list(_installs_grouped)
                count = len(_installs_grouped)
                cost = sum(c for _,_,c in _installs_grouped)
                _gen_campaign(count, campaign_id, cost)

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
        app = account.get_app(app_id)
        if not app:
            continue

        # construct some attributes
        app_name = app['application_name']
        device_campaign_lst = account.generate_install_data(day, app_id)

        for did, campaign_id, cost in device_campaign_lst:
            installs.append({
                "device_ids"    : {"udid": did},
                "app_id"        : app_id,
                "bundle_id"     : app['bundle_id'],
                "campaign_id"   : campaign_id,
                "campaign_name" : DemoData._get_campaign_name(app_name, campaign_id),
                "creative"      : "cats.jpg",
                "incentivized"  : 0,
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
