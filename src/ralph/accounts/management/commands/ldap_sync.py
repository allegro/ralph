# -*- coding: utf-8 -*-
import logging
import sys
import textwrap

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from ldap.controls import SimplePagedResultsControl


logger = logging.getLogger(__name__)
LDAP_RESULTS_PAGE_SIZE = 100

try:
    import ldap
    from django_auth_ldap.backend import _LDAPUser
    ldap_module_exists = True
except ImportError:
    ldap_module_exists = False


def _truncate(field_key, field_name, ldap_dict):
    """
    Truncate user's field when it's longer then default django value, which is
    n chars.
    """
    if field_key in ldap_dict:
        max_length = get_user_model()._meta.get_field(field_name).max_length
        ldap_dict[field_key] = [
            surname[:max_length] for surname in ldap_dict[field_key]
        ]


def get_ldap():
    """Gets an LDAP object according to the configuration of this instance."""
    conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
    conn.protocol_version = settings.AUTH_LDAP_PROTOCOL_VERSION
    conn.simple_bind_s(
        settings.AUTH_LDAP_BIND_DN,
        settings.AUTH_LDAP_BIND_PASSWORD,
    )
    return conn


class Command(BaseCommand):

    """Refresh info about users from ldap."""
    help = textwrap.dedent(__doc__).strip()

    def _create_or_update_user(self, user_dn, ldap_dict):
        username = ldap_dict[settings.AUTH_LDAP_USER_USERNAME_ATTR][0]
        ldap_user = _LDAPUser(self.backend, username=username.lower())
        ldap_user._user_dn = user_dn
        ldap_user._user_attrs = ldap_dict
        ldap_user.populate_user()

    def _disconnect(self):
        self.conn.unbind_s()

    def _run_ldap_query(self, query):
        self.conn = get_ldap()
        try:
            lc = SimplePagedResultsControl(
                size=LDAP_RESULTS_PAGE_SIZE,
                cookie=''
            )
            msgid = self.conn.search_ext(
                settings.AUTH_LDAP_USER_SEARCH_BASE,
                ldap.SCOPE_SUBTREE,
                query,
                serverctrls=[lc],
            )
            page_num = 0
            while True:
                page_num += 1
                r_type, r_data, r_msgid, serverctrls = self.conn.result3(msgid)
                self.stdout.write("Pack of %s users loaded (page %s)" % (
                    LDAP_RESULTS_PAGE_SIZE,
                    page_num,
                ))
                for item in r_data:
                    yield item
                if serverctrls:
                    if serverctrls[0].cookie:
                        lc.size = LDAP_RESULTS_PAGE_SIZE
                        lc.cookie = serverctrls[0].cookie
                        msgid = self.conn.search_ext(
                            settings.AUTH_LDAP_USER_SEARCH_BASE,
                            ldap.SCOPE_SUBTREE,
                            query,
                            serverctrls=[lc],
                        )
                    else:
                        break
                else:
                    logger.error(
                        'LDAP::_run_ldap_query\tQuery: %s\t'
                        'Server ignores RFC 2696 control',
                    )
                    sys.exit(1)
        finally:
            self._disconnect()

    def _get_users(self):
        objcls = settings.LDAP_SERVER_OBJECT_USER_CLASS
        try:
            user_filter = settings.AUTH_LDAP_USER_FILTER
        except AttributeError:
            query = '(objectClass=%s)' % (objcls,)
        else:
            query = '(&(objectClass=%s)%s)' % (objcls, user_filter,)
        ldap_users = self._run_ldap_query(query)
        return ldap_users

    def _load_backend(self):
        path = settings.AUTHENTICATION_BACKENDS[0].split('.')
        module_path = path[:-1]
        class_name = path[-1]
        module = __import__('.'.join(module_path), globals(), locals(),
                            class_name)
        self.backend = getattr(module, class_name)()

    def check_settings_existence(self):
        """Check if all needed settings are defined in settings.py"""
        options = [
            'AUTH_LDAP_SERVER_URI',
            'AUTH_LDAP_USER_SEARCH_BASE',
            'AUTH_LDAP_USER_USERNAME_ATTR',
            'AUTH_LDAP_PROTOCOL_VERSION',
            'AUTH_LDAP_BIND_DN',
            'AUTH_LDAP_BIND_PASSWORD',
        ]
        for option in options:
            if not hasattr(settings, option):
                logger.error(
                    'LDAP::check_settings_existence\tSetting %s '
                    'is not provided.' % option
                )
                self.stdout.write("Setting '%s' is not provided." % option)
                sys.exit(1)

    def handle(self, *args, **kwargs):
        """Load users from ldap command."""
        self.check_settings_existence()
        self._load_backend()
        self.stdout.write("Syncing...")
        if not ldap_module_exists:
            logger.error("ldap module not installed")
            raise ImportError("No module named ldap")
        synced = self.populate_users()
        self.stdout.write("LDAP users synced: {}".format(synced))

    def populate_users(self):
        """Load users from ldap and populate them. Returns number of users."""
        synced = 0
        for user_dn, ldap_dict in self._get_users():
            _truncate('sn', 'last_name', ldap_dict)
            self._create_or_update_user(user_dn, ldap_dict)
            synced += 1
        return synced
