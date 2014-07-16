#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging


logger = logging.getLogger(__name__)


try:
    from django_auth_ldap.config import ActiveDirectoryGroupType
    from django_auth_ldap.backend import (
        populate_user,
        populate_user_profile,
        LDAPSettings,
    )
except ImportError:
    logger.debug("django_auth_ldap package not provided")
else:
    from django.dispatch import receiver
    from django.conf import settings
    from django.utils.encoding import force_unicode
    from lck.django import cache

    # Add default value to LDAPSetting dict. It will be replaced by
    # django_auth_ldap with value in settings.py and visible for each
    # ldap_user.
    LDAPSettings.defaults['GROUP_MAPPING'] = {}
    GROUP_CACHE_TIMEOUT = 1200

    @receiver(populate_user)
    def staff_superuser_populate(sender, user, ldap_user, **kwargs):
        user.is_superuser = 'superuser' in ldap_user.group_names
        user.is_staff = 'staff' in ldap_user.group_names
        user.is_active = 'active' in ldap_user.group_names

    @receiver(populate_user_profile)
    def manager_attribute_populate(sender, profile, ldap_user, **kwargs):
        try:
            profile_map = settings.AUTH_LDAP_PROFILE_ATTR_MAP
        except AttributeError:
            profile_map = {}
        if 'manager' in profile_map:
            if profile_map['manager'] in ldap_user.attrs:
                manager_ref = ldap_user.attrs[profile_map['manager']][0]
                # CN=John Smith,OU=TOR,OU=Corp-Users,DC=mydomain,DC=internal
                manager_ref = manager_ref.decode('utf-8')
                cn = manager_ref.split(',')[0][3:]
                profile.manager = cn

    class MappedGroupOfNamesType(ActiveDirectoryGroupType):

        """Provide group mappings described in project settings."""

        def _group_cache_key(self, group_dn):
            return force_unicode(group_dn).replace(' ', '_').replace('\n', '')

        def _get_group(self, group_dn, ldap_user, group_search):
            key = self._group_cache_key(group_dn)
            group = cache.get(key)
            if not group:
                base_dn = group_search.base_dn
                group_search.base_dn = force_unicode(group_dn)
                group = group_search.execute(ldap_user.connection)[0]
                group_search.base_dn = base_dn
                cache.set(key, group, timeout=GROUP_CACHE_TIMEOUT)
            return group

        def user_groups(self, ldap_user, group_search):
            """Get groups which user belongs to."""
            self._ldap_groups = ldap_user.settings.GROUP_MAPPING
            group_map = []

            try:
                group_dns = ldap_user.attrs['memberOf']
            except KeyError:
                group_dns = []
            # if mapping defined then filter groups to mapped only
            if self._ldap_groups:
                group_dns = filter(lambda x: x in self._ldap_groups, group_dns)
            for group_dn in group_dns:
                group = self._get_group(group_dn, ldap_user, group_search)
                group_map.append(group)

            return group_map

        def group_name_from_info(self, group_info):
            """Map ldap group names into ralph names if mapping defined."""
            if self._ldap_groups:
                for dn in group_info[1]['distinguishedname']:
                    mapped = self._ldap_groups.get(dn)
                    if mapped:
                        return mapped
            # return original name if mapping not defined
            else:
                return super(
                    MappedGroupOfNamesType,
                    self
                ).group_name_from_info(group_info)
