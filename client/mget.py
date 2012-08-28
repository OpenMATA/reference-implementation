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
    auth = auth.encode('base64').rstrip()
    req.add_header("Authorization", "Basic %s" % auth)

    # 2. http fetch
    resp = urllib2.urlopen(req)
    print '  %s %s (%s)' % (resp.code, resp.msg, resp.headers.get('content-length','n/a'))
    content = resp.read()
    out.write(content)

    # 3. parse json
    content = json.loads(content)

    return content



def run(args):
    with output_logging(args, '0000-00-00', 'application_list') as (out, out_filename):
        url = args.base_url + '/v1/application_list'
        output_str = ' -> %s' % out_filename if out_filename else ''
        print 'Fetch %s%s' % (url, output_str)
        content = fetch_json(args, out, url)

        data = content.get('data',[])
        print 'Fetched %s applications' % len(data)
        for i, item in enumerate(data):
            print '%-2d %s (%s)' % (i, item.get('application_name','?'), item.get('app_id','?'))


def main():
    today = datetime.date.today().isoformat()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-u', '--user', required=True, help='user')
    parser.add_argument('-p', '--password', help='password')
    parser.add_argument('-a', '--app-id', help='app_id')
    parser.add_argument('-o', '--output', help='Save http fetch in files. Filenames are {output_dir}/{date}{end_point}{output}.')
    parser.add_argument('-x', action='store_true', help='Validate MATA result in strict mode')
    parser.add_argument('base_url', default=DEFAULT_BASE_URL, nargs='?', help='Base URL')
    parser.add_argument('start', default=today, nargs='?', help='start date yyyy-mm-dd (default today)')
    parser.add_argument('end', default=today, nargs='?', help='end date yyyy-mm-dd (default today)')
    args = parser.parse_args()

    if not args.password:
        args.password = getpass.getpass("Password: ")

    if args.output:
        head, tail = os.path.split(args.output)
        args.output_template = '%s%%(date)s.%%(end_point)s.%s' % (head, tail)

    if args.x:
        raise NotImplementedError()

    # take no trailing slash convention
    args.base_url = args.base_url.rstrip('/')

    print args
    run(args)


if __name__ =='__main__':
    main()
