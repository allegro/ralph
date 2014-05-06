# -*- coding: utf-8 -*-
"""LDAP utilities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import ldap

from django.conf import settings


def get_ldap():
    """Gets an LDAP object according to the configuration of this instance."""
    conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
    conn.protocol_version = settings.AUTH_LDAP_PROTOCOL_VERSION
    conn.simple_bind_s(
        settings.AUTH_LDAP_BIND_DN,
        settings.AUTH_LDAP_BIND_PASSWORD,
    )
    return conn
