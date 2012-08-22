"""
Sample Data Model that generates deterministic random data.

"""

import argparse
import datetime
import hashlib


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
    'test1': dict(username='test1', password='pass', app_ids=['12341', '12342', '12343']),
    'test2': dict(username='test2', password='pass', app_ids=['12351', '12352']),
    'test3': dict(username='test3', password='pass', app_ids=[DANGER_STR]),
    }

    APPLICATIONS = {
    '12341'   : {"app_id": "12341",   "application_name": 'Best Game Ever',       "bundle_id": "com.foo.best_game"     , "base_install": 10, "rand_install": 10 },
    '12342'   : {"app_id": "12342",   "application_name": u'\u4e09\u570b\u5fd73', "bundle_id": "com.foo.three_kingdom3", "base_install": 10, "rand_install": 10 },
    '12343'   : {"app_id": "12343",   "application_name": 'Didgeridoo',           "bundle_id": "com.foo.didgeridoo"    , "base_install": 25, "rand_install": 10 },
    '12351'   : {"app_id": "12351",   "application_name": 'Test app2',            "bundle_id": "com.bar.test_app2"     , "base_install": 10, "rand_install": 10 },
    '12352'   : {"app_id": "12352",   "application_name": u'\u6c34\u6ef8\u50b3',  "bundle_id": "com.bar.water_margin"  , "base_install": 10, "rand_install": 10 },
    DANGER_STR: {"app_id": DANGER_STR,"application_name": DANGER_STR ,            "bundle_id": "com.test.danger"       , "base_install": 10, "rand_install": 10 },
    }

    BASE_INSTALL = 16


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


    def generate_install_data(self, date, app_id):
        """
        Deterministic random algorithm to generate list of device id for a day

        @returns: list of (device_id, campaign_id)
        """
        msg = 'some deterministic msg %s,%s' % (date,app_id)
        h = hashlib.md5(msg)
        # a random number in [0, 1)
        r0 = ord(h.digest()[-1]) / 256.0

        app = self.get_app(app_id)

        num_installs = int(app['base_install'] + app['rand_install']*r0)

        result = []
        for i in xrange(num_installs):
            h.update('tada %s' % i)
            did = h.hexdigest()

            # simple rule to split the install into two campaigns
            campaign_id = 10 + (i % 2)

            result.append((did, campaign_id))

        return result


    @staticmethod
    def _get_campaign_name(app_name, campaign_id):
        return "%s campaign-%s" % (app_name, campaign_id)



def main():
    today = datetime.date.today().isoformat()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-u', default='test1', help='user')
    parser.add_argument('-p', default='pass', help='password')
    parser.add_argument('-a', default='12343', help='app_id')
    parser.add_argument('date', default=today, nargs='?', help='date (default today)')
    args = parser.parse_args()

    acc = DemoData(args.u, args.p)
    device_ids = acc.get_install_device_id(args.date, args.a)
    print 'date      : %s' % args.date
    print 'app_ids   : %s' % acc.get_app_ids()
    print 'app       : %s' % acc.get_app(args.a)
    print 'device_ids: %s' % len(device_ids)

    for did in device_ids:
        print '  ', did


if __name__ =='__main__':
    main()
