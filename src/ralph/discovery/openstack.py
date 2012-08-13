# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import urllib
import urllib2
import json
import datetime


class Error(Exception):
    pass


class OpenStack(object):
    def __init__(self, url, user, password):
        self.auth_url = url
        self.user = user
        self.public_url, self.auth_token = self.auth(password)

    def auth(self, password):
        auth_url = '/'.join([self.auth_url, 'v2.0/tokens'])
        auth_data = json.dumps({
            'auth': {
                'tenantName': self.user,
                'passwordCredentials': {
                    'username': self.user,
                    'password': password,
                },
            },
        })
        auth_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        request = urllib2.Request(auth_url, auth_data, auth_headers)
        auth_reply = json.loads(urllib2.urlopen(request).read())
        for service in auth_reply['access']['serviceCatalog']:
            if service['name'] == 'nova':
                public_url = service['endpoints'][0]['publicURL']
                break
        else:
            raise Error('Service "nova" not available')
        auth_token = auth_reply['access']['token']['id']
        return public_url, auth_token

    def query(self, query, url=None, **kwargs):
        query_args = urllib.urlencode(kwargs)
        query_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Project-Id': self.user,
            'X-Auth-Token': self.auth_token,
        }
        query_url = '/'.join([
                url or self.public_url,
                query,
            ]) + '?' + query_args
        request = urllib2.Request(query_url, headers=query_headers)
        return json.loads(urllib2.urlopen(request).read())

    def simple_tenant_usage(self, start=None, end=None):
        if end is None:
            end = datetime.datetime.now()
        if start is None:
            start = end - datetime.timedelta(hours=24)
        return self.query(
                'os-simple-tenant-usage',
                start=start.strftime('%Y-%m-%dT%H:%M:%S'),
                end=end.strftime('%Y-%m-%dT%H:%M:%S'),
            )['tenant_usages']


