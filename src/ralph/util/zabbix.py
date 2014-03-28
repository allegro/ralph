#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from pyzabbix import ZabbixAPI


class Zabbix(object):

    def __init__(self, url, user, password):
        self.zapi = ZabbixAPI(url, log_level=0)
        self.zapi.login(user, password)

    def get_all_hosts(self):
        return self.zapi.host.get(select_profile='extend',
                                  output='extend')

    def get_current_triggers(self):
        params = dict(output='extend', expandData='host', monitored='true',
                      active='true', expandDescription='true',
                      sortorder='DESC', status=0, only_true='true')
        return list(self.zapi.trigger.get(**params))

    def get_all_triggers(self, host=None):
        params = dict(output='extend', expandData='host', monitored='true',
                      sortfield='lastchange', expandDescription='true',
                      status=0, sortorder='DESC')
        if host is not None:
            params.update(hostids=[host])
        return list(self.zapi.trigger.get(**params))

    def get_host_by_name(self, host_name):
        hosts = self.zapi.host.get(filter={"host": host_name})
        if not hosts:
            raise KeyError('No such host')
        elif len(hosts) > 1:
            raise ValueError('Multiple hosts found')
        return hosts[0]

    def get_or_create_host(self, host_name, ip, group_id):
        try:
            host = self.get_host_by_name(host_name)
        except KeyError:
            hostids = self.zapi.host.create(
                host=host_name,
                groups=[{
                        'groupid': group_id,
                        }],
                interfaces=[{
                    'main': 1,
                    'type': 1,
                    'useip': 1,
                    'dns': '',
                    'port': 10050,
                    'ip': ip,
                }],
                templates=[],
                inventory=[],
            )
            hosts = self.zapi.host.get(
                filter={"hostid": hostids['hostids'][0]})
            host = hosts[0]
        return host

    def get_or_create_template_id(self, template_name, group_id):
        template = {
            'host': template_name,
            'groups': [{
                'groupid': group_id,
            }],
        }
        templates = self.zapi.template.get(filter=template)
        if not templates:
            ret = self.zapi.template.create(template)
            template_id = ret['templateids'][0]
        else:
            template_id = templates[0]['templateid']
        return template_id

    def get_group_id(self, group_name):
        return self.zapi.hostgroup.get(filter={'name': group_name})[0]['groupid']

    def set_host_templates(self, host_name, ip, template_names, group_name):
        group_id = self.get_group_id(group_name)
        host = self.get_or_create_host(host_name, ip, group_id)
        template_ids = [self.get_or_create_template_id(template_name, group_id)
                        for template_name in template_names]
        self.zapi.host.update({
            'hostid': host['hostid'],
            'templates': [{'templateid': tid} for tid in template_ids],
        })
