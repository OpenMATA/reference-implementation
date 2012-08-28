"""
MATA Test Client

By default it pulls from the MATA test server at

    http://test-server.openmata.org/

"""

from __future__ import with_statement
import argparse
import contextlib
import datetime
import getpass
import os
import StringIO
import traceback
import urllib
import urllib2

try:
    import json
except ImportError:
    import simplejson as json

DEFAULT_BASE_URL = "http://test-server.openmata.org/"



@contextlib.contextmanager
def output_logging(args, date, end_point):
    if args.output:
        out_filename = args.output_template % dict(date=date, end_point=end_point)
        out = open(out_filename,'wb')
    else:
        # dummy sink
        out_filename = ''
        out = StringIO.StringIO()

    try:
        yield out, out_filename

    except:
        # just log the error and then move on
        err = traceback.format_exc()
        out.write(err)
        print err

    finally:
        out.close()



def fetch_json(args, out, url, data=None):
    """
    HTTP Fetching with error reporting and output logging.
    """
    content = None

    # 1. request and basic authentication
    req = urllib2.Request(url, data=data)
    auth = '%s:%s' % (args.user, args.password)
    auth = auth.encode('base64')
    # By default long base64 string are broken into multiple lines. Join them into single line. Also drop the trailing \n.
    auth = auth.replace('\n','')
    req.add_header("Authorization", "Basic %s" % auth)

    # 2. http fetch
    resp = urllib2.urlopen(req)
    print '  %s %s (%s)' % (resp.code, resp.msg, resp.headers.get('content-length','n/a'))
    content = resp.read()
    out.write(content)

    # 3. parse json
    content = json.loads(content)

    return content



def mata_get_app(args):
    with output_logging(args, '0000-00-00', 'application_list') as (out, out_filename):
        url = args.base_url + '/v1/application_list'
        output_str = ' -> %s' % out_filename if out_filename else ''
        print 'Fetch %s%s' % (url, output_str)
        content = fetch_json(args, out, url)

        assert isinstance(content, dict)
        data = content.get('data',[])
        print 'Found %s applications' % len(data)
        for i, item in enumerate(data):
            print '  %2d %s (%s)' % (i, item.get('application_name','?'), item.get('app_id','?'))


def mata_get_agg(args):
    with output_logging(args, args.start, 'campaign_aggregate') as (out, out_filename):

        params = {'start_day': args.start, 'end_day': args.end}
        if args.app_id:
            params['app_id'] = args.app_id

        url = args.base_url + '/v1/campaign_aggregate?' + urllib.urlencode(params)

        output_str = ' -> %s' % out_filename if out_filename else ''
        print 'Fetch %s%s' % (url, output_str)
        content = fetch_json(args, out, url)

        assert isinstance(content, dict)
        data = content.get('data',[])

        FORMAT = '%-10s %-10s %-40s %8s %8s %8s %8s'
        print
        print FORMAT % ('day', 'app_id', 'campaign', 'imp', 'clicks', 'download', 'spend')
        print '-' * 100

        for i, item in enumerate(data):
            print FORMAT % (
                item.get('day'          , '?'),
                item.get('app_id'       , '?'),
                item.get('campaign_name', '?'),
                item.get('impressions'  , '?'),
                item.get('clicks'       , '?'),
                item.get('downloads'    , '?'),
                item.get('spend'        , '?'),
                )


def mata_get_ins(args):
    with output_logging(args, args.start, 'installs') as (out, out_filename):

        params = {'day': args.start}
        if args.app_id:
            params['app_id'] = args.app_id

        url = args.base_url + '/v1/installs?' + urllib.urlencode(params)

        output_str = ' -> %s' % out_filename if out_filename else ''
        print 'Fetch %s%s' % (url, output_str)
        content = fetch_json(args, out, url)

        assert isinstance(content, dict)
        data = content.get('data',[])

        installs = data.get('installs',[])
        print 'Found %s installs day=%s' % (len(installs), data.get('day'))
        for i, item in enumerate(installs):
            print '  %2d %s app_id=%s campaign_name="%s"' % (i, item.get('device_ids','?'), item.get('app_id','?'), item.get('campaign_name','?'))


def main():
    today = datetime.date.today().isoformat()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-u', '--user', required=True, help='user')
    parser.add_argument('-p', '--password', help='password')
    parser.add_argument('-e', '--end-point', default='app', choices=['app', 'agg', 'ins'], help='Select the MATA end_point')
    parser.add_argument('-a', '--app-id', help='app_id')
    parser.add_argument('-o', '--output', help='Save http fetch in files. Filenames are augmented with date string.')
    parser.add_argument('-x', action='store_true', help='Validate MATA result in strict mode (to be implemented)')
    parser.add_argument('base_url', default=DEFAULT_BASE_URL, nargs='?', help='Base URL')
    parser.add_argument('start', default=today, nargs='?', help='start date yyyy-mm-dd (default today)')
    parser.add_argument('end', default=today, nargs='?', help='end date yyyy-mm-dd (default today)')
    args = parser.parse_args()

    #print args

    if not args.password:
        args.password = getpass.getpass("Password: ")

    if args.output:
        head, tail = os.path.split(args.output)
        args.output_template = '%s%s%%(date)s.%%(end_point)s.%s' % (head, ('/' if head else ''), tail)

    if args.x:
        raise NotImplementedError()

    # take the no trailing slash convention
    args.base_url = args.base_url.rstrip('/')

    get_method = globals()['mata_get_%s' % args.end_point]
    get_method(args)



if __name__ =='__main__':
    main()
