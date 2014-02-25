#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging


logger = logging.getLogger(__name__)


try:
    from django_auth_ldap.config import NestedGroupOfNamesType
    from django_auth_ldap.backend import populate_user, LDAPSettings
except ImportError:
    logger.debug("django_auth_ldap package not provided")
else:
    from django.dispatch import receiver

    # Add default value to LDAPSetting dict. It will be replaced by
    # django_auth_ldap with value in settings.py and visible for each
    # ldap_user.
    LDAPSettings.defaults['GROUP_MAPPING'] = {}


    @receiver(populate_user)
    def staff_superuser_populate(sender, user, ldap_user, **kwargs):
        user.is_superuser = 'superuser' in ldap_user.group_names
        user.is_staff = 'staff' in ldap_user.group_names

    class MappedNestedGroupOfNamesType(NestedGroupOfNamesType):
        """Provide group mappings described in project settings."""

        def user_groups(self, ldap_user, group_search):
            # filter groups to these presents in config
            group_map = super(MappedNestedGroupOfNamesType,
                              self).user_groups(ldap_user, group_search)
            self._ldap_groups = ldap_user.settings.GROUP_MAPPING
            group_map = [
                group for group in group_map
                if group[1][self.name_attr][0] in self._ldap_groups.keys()
            ]
            return group_map

        def group_name_from_info(self, group_info):
            # map ldap group names into ralph group names
            name = super(MappedNestedGroupOfNamesType, self).group_name_from_info(group_info)
            mapped = self._ldap_groups[name]
            return mapped
