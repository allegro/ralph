#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pyzabbix import ZabbixAPI
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

connection = False

def initiate_connection():
    global connection
    logger.error('Initiating connection')
    login=settings.ZABBIX_USER
    passwd=settings.ZABBIX_PASSWORD
    connection = ZabbixAPI(server=settings.ZABBIX_URL,
            log_level=0,
    )
    connection.login(login, passwd)

def get_all_hosts():
    if not connection:
        initiate_connection()
    return connection.host.get(select_profile='extend', output='extend')

def get_current_triggers():
    if not connection:
        initiate_connection()
    # status=0 -> STATUS_PROBLEM
    return [ x for x in connection.trigger.get(
        output='extend',
        expandData='host',
        monitored='true',
        active='true',
        expandDescription='true',
        sortorder='DESC',
        status=0,
        only_true='true',
    )]

def get_all_triggers(host=None):
    # status=0 -> STATUS_PROBLEM
    if not connection:
        initiate_connection()
    params = dict(
        output='extend',
        expandData='host',
        monitored='true',
        sortfield='lastchange',
        expandDescription='true',
        status=0,
        sortorder='DESC',
    )
    if host:
        params.update(dict(hostids=[host]))
    return [ x for x in connection.trigger.get(**params)]


