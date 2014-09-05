# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import httplib
import socket
import threading
import urllib2

from rq.timeouts import JobTimeoutException
from ssl import SSLError


FAMILIES = {
    'GoAhead-Webs': 'Thomas-Krenn',
    'Apache': 'Apache',
    'Sun-ILOM-Web-Server': 'Sun',
    'Virata-EmWeb': 'SSG',
    'Allegro-Software-RomPager': 'RomPager',
    'cisco-IOS': 'Cisco',
    'IBM_HTTP_Server': 'IBM',
    '': 'Unspecified',
}


class HTTPRedirectHandler(urllib2.HTTPRedirectHandler):

    def http_error_302(self, req, fp, code, msg, headers):
        return urllib2.HTTPRedirectHandler.http_error_302(self, req, fp,
                                                          code, msg, headers)
    http_error_301 = http_error_303 = http_error_307 = http_error_302


def get_http_info(ip):
    opener = urllib2.build_opener()
    request = urllib2.Request("http://{}".format(ip))
    try:
        response = opener.open(request, timeout=5)
    except urllib2.HTTPError as e:
        response = e
    except (
        urllib2.URLError, httplib.BadStatusLine, httplib.InvalidURL,
        socket.timeout, SSLError, socket.error,
    ):
        request = urllib2.Request("https://{}".format(ip))
        try:
            response = opener.open(request, timeout=5)
        except urllib2.HTTPError as e:
            response = e
        except (
            urllib2.URLError, httplib.BadStatusLine, httplib.InvalidURL,
            socket.timeout, SSLError, socket.error,
        ):
            request = urllib2.Request(
                "https://{}".format(':'.join((ip, '8006')))  # for Proxmox
            )
            try:
                response = opener.open(request, timeout=5)
            except urllib2.HTTPError as e:
                response = e
            except (
                urllib2.URLError, httplib.BadStatusLine, httplib.InvalidURL,
                socket.timeout, SSLError, socket.error,
            ):
                return {}, ''

    def closer():
        try:
            response.close()
        except JobTimeoutException as e:
            raise e
        except:
            pass

    threading.Timer(5, closer).start()
    try:
        document = response.read().decode('utf-8', 'ignore')
    finally:
        try:
            response.close()
        except JobTimeoutException as e:
            raise e
        except:
            pass
    headers = response.headers
    return headers, document


def guess_family(headers, document):
    server = headers.get('Server', '')
    if '/' in server:
        server = server.split('/', 1)[0]
    family = FAMILIES.get(server, server)
    if family in ('Apache', 'Unspecified'):
        if '<div id="copyright">Copyright &copy; IBM Corporation' in document:
            family = 'IBM'
        elif '<title>Proxmox Virtual Environment</title>' in document:
            family = 'Proxmox'
        elif 'Cisco Systems, Inc. All rights' in document:
            family = 'Cisco'
        elif any((
            '<title>BIG-IP' in document,
            'mailto:support@f5.com' in document,
        )):
            family = 'F5'
        elif 'APC Management Web Server' in document:
            family = 'APC'
        elif any((
            'Hewlett-Packard Development Company' in document,
            'HP BladeSystem Onboard Administrator' in document,
        )):
            family = 'HP'
        elif any((
            'Welcome to VMware ESX Server' in document,
            'VMware ESXi' in document,
        )):
            family = 'ESX'
        elif 'ATEN International Co Ltd.' in document:
            family = 'Thomas-Krenn'
    elif family in ('lighttpd',):
        if 'Modular Server Control' in document:
            family = 'Modular'
        elif '<title>IMM</title>' in document:
            family = 'IBM System X'
    elif family in ('Thomas-Krenn',):
        if 'ERIC_RESPONSE_OK' in document:
            family = 'VTL'
    elif family in ('Mbedthis-Appweb', 'Embedthis-Appweb'):
        if '/sclogin.html?console' in document:
            family = 'Dell'
        elif 'Juniper' in document:
            family = 'Juniper'
    elif family in ('pve-api-daemon',):
        family = 'Proxmox'
    return family


def get_http_family(ip):
    headers, document = get_http_info(ip)
    family = guess_family(headers, document)
    return family
