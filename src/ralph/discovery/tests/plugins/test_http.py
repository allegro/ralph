# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase
import mock

from ralph.discovery.plugins import http_supermicro
from ralph.discovery.http import guess_family


class HttpPluginTest(TestCase):

    def test_guess_family_empty(self):
        family = guess_family({}, '')
        self.assertEqual(family, 'Unspecified')

    def test_guess_family_sun(self):
        family = guess_family({'Server': 'Sun-ILOM-Web-Server'}, '')
        self.assertEqual(family, 'Sun')

    def test_guess_family_f5(self):
        family = guess_family({'Server': 'Apache'}, '<title>BIG-IP</title>')
        self.assertEqual(family, 'F5')

    def test_guess_family_juniper(self):
        test_string = '<title>Log In - Juniper Web Device Manager</title>'
        family = guess_family({'Server': 'Mbedthis-Appweb/2.4.2'},
                              test_string)
        self.assertEqual(family, 'Juniper')

    def test_guess_family_dell(self):
        test_string = 'top.document.location.href = "/sclogin.html?console"'
        family = guess_family({'Server': 'Mbedthis-Appweb/2.4.2'},
                              test_string)
        self.assertEqual(family, 'Dell')


class HttpSupermicroPluginTest(TestCase):

    def test_macs(self):
        opener = mock.Mock()
        request_session = mock.Mock()
        request_session.raw = """\
//Dynamic Data Begin

 WEBVAR_JSONVAR_WEB_SESSION =

 {

 WEBVAR_STRUCTNAME_WEB_SESSION :

 [

 { 'SESSION_COOKIE' : 'xmBo2KB9rZCknX73xSfoy0DiMxXua3Fk001' },  {} ],

 HAPI_STATUS:0 };

//Dynamic data end


"""
        request_macs = mock.Mock()
        request_macs.raw = """\
//Dynamic Data Begin

 WEBVAR_JSONVAR_GETMBMAC =

 {

 WEBVAR_STRUCTNAME_GETMBMAC :

 [

 { 'MAC1' : '00:25:90:1E:BF:22','MAC2' : '00:25:90:1E:BF:23' },  {} ],

 HAPI_STATUS:0 };

//Dynamic data end



"""
        request_mgmt = mock.Mock()
        request_mgmt.raw = """\
//Dynamic Data Begin

 WEBVAR_JSONVAR_HL_GETLANCONFIG =

 {

 WEBVAR_STRUCTNAME_HL_GETLANCONFIG :

 [

 { 'IPAddrSource' : 1,'MAC' : '00:25:90:2C:E5:CC','IP' : '10.235.29.201','Mask' : '255.255.0.0','Gateway' : '10.235.0.1','PrimaryDNS' : '10.10.10.1','SecondaryDNS' : '','VLanEnable' : 0,'VLANID' : 0 },  {} ],

 HAPI_STATUS:0 };

//Dynamic data end


"""

        def open_side(request, timeout):
            response = mock.Mock()
            response.readlines.return_value = request.raw.splitlines()
            return response
        opener.open.side_effect = open_side

        def request_side(url, *args, **kwargs):
            if url.endswith('WEBSES/create.asp'):
                return request_session
            elif url.endswith('rpc/getmbmac.asp'):
                return request_macs
            elif url.endswith('rpc/getnwconfig.asp'):
                return request_mgmt
        with mock.patch('ralph.discovery.plugins.http_supermicro.urllib2') as urllib2:
            urllib2.build_opener.return_value = opener
            urllib2.Request.side_effect = request_side
            macs = http_supermicro._get_macs('127.0.0.1')
        self.assertEquals(macs, {
            'IPMI MC': '00:25:90:2C:E5:CC',
            'MAC2': '00:25:90:1E:BF:23',
            'MAC1': '00:25:90:1E:BF:22'
        })
