# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings
from django.test import TestCase
from mock import patch

from ralph.cmdb.models_ci import (
    CI,
)
from ralph.cmdb.integration.sync import ZabbixImporter


zabbix_api_response = [{
    'available': '1', 'maintenance_type': '0',
    'maintenances': [], 'ipmi_username': '', 'snmp_disable_until': '0',
    'ipmi_authtype': '-1', 'ipmi_disable_until': '0', 'lastaccess': '0',
    'snmp_error': '', 'ipmi_privilege': '2', 'jmx_error': '',
    'jmx_available': '0', 'ipmi_errors_from': '0', 'maintenanceid': '0',
    'snmp_available': '0', 'status': '0', 'host': 'hostname.dc2',
    'disable_until': '0', 'ipmi_password': '', 'ipmi_available': '0',
    'maintenance_status': '0', 'snmp_errors_from': '0', 'ipmi_error': '',
    'proxy_hostid': '18699', 'hostid': '10891', 'name': 'hostname.dc2'
    '(venture/devops) [someinfo]', 'jmx_errors_from': '0', 'jmx_disable_until':
    '0', 'error': '', 'maintenance_from': '0', 'errors_from': '0'
}]


class PatchedZabbix(object):
    @classmethod
    def get_all_hosts(cls):
        return zabbix_api_response


class CMDBZabbixTest(TestCase):
    """
    Test Importing Zabbix hosts into the CMDB database
    """

    def setUp(self):
        pass

    @patch('ralph.cmdb.integration.sync.zabbix', PatchedZabbix)
    @patch.object(settings, 'ZABBIX_IMPORT_HOSTS', True)
    def test_zabbix_import_hosts(self):
        ZabbixImporter().import_hosts()
        self.assertEquals(
            [(c.name, c.type.id, c.state, c.status) for c in CI.objects.all()],
            [('hostname.dc2', 2, 1, 2)],
        )

    @patch('ralph.cmdb.integration.sync.zabbix', PatchedZabbix)
    @patch.object(settings, 'ZABBIX_IMPORT_HOSTS', False)
    def test_zabbix_dont_import_hosts(self):
        ZabbixImporter().import_hosts()
        self.assertEquals(
            CI.objects.count(),
            0
        )
