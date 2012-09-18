MATA Reference Implementation
=============================

This is a MATA server reference implementation. The current version of MATA Test Server is hosted at
<http://test-server.openmata.org/>

The test server is written in Python. It has dependency on these software:

- Python 2.5 or above
- simplejson (only needed for Python 2.5)
- Flask

To run MATA test server from source code, use

    python mata_test_server.py

Then connect to it using the URL http://localhost:5000/.


MATA Test Client
================

The MATA Test client **mget** is a client side command line tool to help test a MATA implementation. This is its help page.

    usage: mget.py [-h] -u USER [-p PASSWORD] [-e {app,agg,ins}] [-a APP_ID]
                   [-o OUTPUT] [-x] [-z TZ]
                   [base_url] [start] [end]

    MATA Test Client

    By default it pulls from the MATA test server at

        http://test-server.openmata.org/

    positional arguments:
      base_url              Base URL
      start                 start date yyyy-mm-dd (default today)
      end                   end date yyyy-mm-dd (default today)

    optional arguments:
      -h, --help            show this help message and exit
      -u USER, --user USER  user
      -p PASSWORD, --password PASSWORD
                            password
      -e {app,agg,ins}, --end-point {app,agg,ins}
                            Select the MATA end_point
      -a APP_ID, --app-id APP_ID
                            app_id
      -o OUTPUT, --output OUTPUT
                            Save http content in files. Filenames are augmented with date string.
      -x                    Validate MATA result in strict mode (to be implemented)
      -z TZ, --tz TZ        Time zone (3 letter code)
