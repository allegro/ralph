#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json

from django.conf import settings
from splunklib.client import connect


class Splunk(object):

    """Usage:

    >>> splunk = Splunk('splunk.host', 'splunk.user', '********')
    >>> splunk.start(earliest='-60m')
    >>> while splunk.progress < 100:
    ...    time.sleep(60)
    >>> splunk.results
    [{u'MBytes': u'123.386241', u'sourcetype': u'splunk_kp', u'percent': u'5.48', u'source': u'/opt/kp/log/csFront.log', u'host': u'hostname1', u'lastReceived':
u'Thu 2012-06-07 12:00:34'}, {u'MBytes': u'40.942306', u'sourcetype': u'splunk_istore', u'percent': u'1.82', u'source': u'/tmp/istoreapi_webapi_traffic.log',
u'host': u'hostname2', u'lastReceived': u'Thu 2012-06-07 12:00:34'}, ...]
    """

    query = ('search earliest=%s latest=%s index="_internal" '
             'source="*license_usage.log" | eval lastReceived = _time | '
             'rename h as host b as bytes st as sourcetype s as source | '
             'stats sum(bytes) as bytes max(lastReceived) as lastReceived '
             'by host sourcetype source | eval mbytes=((bytes/1024)/1024) | '
             'fields host sourcetype source mbytes lastReceived | '
             'stats max(lastReceived) as lastReceived sum(mbytes) as MBytes '
             'by host sourcetype source| fieldformat lastReceived = '
             'strftime(lastReceived, "%%a %%F %%T") | eventstats sum(MBytes) '
             'as totalMB | eval percent = round(100*MBytes/totalMB,2) | '
             'fields - totalMB | sort -MBytes')

    def __init__(self, host=settings.SPLUNK_HOST, username=settings.SPLUNK_USER,
                 password=settings.SPLUNK_PASSWORD):
        self.host = str(host)  # sic, unicode fails in the splunk-sdk
        self.username = str(username)
        self.password = str(password)
        self.splunk = connect(host=self.host, username=self.username,
                              password=self.password)
        self.job = None
        self._results = None

    def start(self, earliest='-1d@d', latest='now'):
        if self.job:
            raise ValueError("Report in progress.")
        self.job = self.splunk.jobs.create(self.query % (earliest, latest))
        self._results = None

    @property
    def progress(self):
        """Returns a float with the percent of the report finished. 100.0 means
        report complete."""

        if self._results:
            return 100.0
        if not self.job:
            raise ValueError("No report in progress.")
        stats = self.job.refresh()(
            'isDone',
            'doneProgress',
            'scanCount',
            'eventCount',
            'resultCount')
        progress = float(stats['doneProgress']) * 100
        if progress > 99.9:
            if stats['isDone'] == '1':
                progress = 100.0
                self._results = self.job.results(output_mode='json',
                                                 count=0).read()
                self.job = None
            else:
                progress = 99.9
        return progress

    @property
    def results(self):
        """Returns a list of results for each host per source-type."""
        if not self._results and self.progress < 100.0:
            raise ValueError("Report still in progress.")
        return json.loads(self._results)
