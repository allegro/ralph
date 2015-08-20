# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

import requests


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
REQUEST_KWARGS = {
    'timeout': 5,
    'verify': False,
    'allow_redirects': False,
}

logger = logging.getLogger(__name__)


def http_get_method(session, url):
    """
    Handle redirects by manual way without fetching content
    (forced by stream=True) to avoid hanged request when content length is 0.
    """
    response = session.get(url, stream=True, **REQUEST_KWARGS)
    if response.status_code in (301, 302) and response.headers.get('location'):
        return http_get_method(session, response.headers['location'])
    return response


def get_http_info(ip):
    headers, content = {}, ''
    url = "http://{}".format(ip)
    with requests.Session() as session:
        try:
            response = http_get_method(session, url)
            response.raise_for_status()
            headers, content = response.headers, response.content
        except requests.exceptions.HTTPError as e:
            logger.error("HTTPERROR: {} for url: {}".format(e, url))
        except requests.exceptions.RequestException as e:
            logger.error("Exception: {} for url: {}".format(e, url))
            url = "https://{}".format(':'.join((ip, '8006')))  # for Proxmox
            try:
                response = http_get_method(session, url)
                response.raise_for_status()
                headers, content = response.headers, response.content
            except requests.exceptions.RequestException as e:
                logger.error("Exception: {} for url: {}".format(e, url))
                url = "https://{}/login.html".format(ip)
                try:
                    response = http_get_method(session, url)
                    response.raise_for_status()
                    headers, content = response.headers, response.content
                except requests.exceptions.RequestException as e:
                    logger.error("Exception: {} for url: {}".format(e, url))
    return headers, content


def guess_family(headers, document):
    document = document.decode("utf8")
    server = headers.get('server', '')
    if '/' in server:
        server = server.split('/', 1)[0]
    family = FAMILIES.get(server, server)
    if family in ('Apache', 'Unspecified'):
        if '<div id="copyright">Copyright &copy; IBM Corporation' in document:
            family = 'IBM'
        elif 'pve2' in document:
            family = 'Proxmox2'
        elif '<title>Proxmox Virtual Environment</title>' in document:
            family = 'Proxmox1'
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
        elif 'XenServer' in document:
            family = 'Xen'
    elif family in ('lighttpd',):
        if 'Modular Server Control' in document:
            family = 'Modular'
        elif '<title>IMM</title>' in document:
            family = 'IBM System X'
    elif family in ('Thomas-Krenn',):
        if 'ERIC_RESPONSE_OK' in document:
            family = 'VTL'
    elif family in ('Mbedthis-Appweb', 'Embedthis-Appweb', 'Embedthis-http'):
        if 'sclogin.html' in document:
            family = 'Dell'
        elif 'Juniper' in document:
            family = 'Juniper'
    if 'pve-api-daemon' in family:
        family = 'Proxmox3'
    if 'sclogin.html' in document:
        family = 'Dell'
    return family


def get_http_family(ip):
    headers, document = get_http_info(ip)
    family = guess_family(headers, document)
    return family
