# -*- coding: utf-8 -*-
import logging

from django.conf import settings
from django.utils.encoding import force_text
from django_auth_ldap.config import ActiveDirectoryGroupType

logger = logging.getLogger(__name__)


class MappedGroupOfNamesType(ActiveDirectoryGroupType):
    """Provide group mappings described in project settings."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ldap_groups = None

    @property
    def ldap_groups(self):
        """
        Composition of flat LDAP groups (taken from `AUTH_LDAP_GROUP_MAPPING`)
        and nested groups (taken from `AUTH_LDAP_NESTED_GROUPS`).

        Returns: dict with both flat and nested LDAP groups.
        """
        if not self._ldap_groups:
            logger.debug("Evaluating LDAP groupd from settings")
            self._ldap_flat_groups = getattr(settings, "AUTH_LDAP_GROUP_MAPPING", {})
            self._ldap_nested_groups = getattr(settings, "AUTH_LDAP_NESTED_GROUPS", {})
            self._ldap_groups = self._ldap_flat_groups.copy()
            self._ldap_groups.update(self._ldap_nested_groups)
        return self._ldap_groups

    def _get_group(self, group_dn, ldap_user, group_search):
        base_dn = group_search.base_dn
        group_search.base_dn = force_text(group_dn)
        group = group_search.execute(ldap_user.connection)[0]
        group_search.base_dn = base_dn
        return group

    def user_groups(self, ldap_user, group_search):
        """Get groups which user belongs to."""
        group_map = []

        def handle_groups(groups_dns):
            """
            Compare user groups with groups accepted by Ralph
            (`self.ldap_groups`) and for each in common get LDAP group

            Args:
                groups_dns: set of user groups DNs
            """
            for group_dn in groups_dns & set(self.ldap_groups.keys()):
                group = self._get_group(group_dn, ldap_user, group_search)
                group_map.append(group)

        username = ldap_user.attrs[settings.AUTH_LDAP_USER_USERNAME_ATTR][0]

        # handle flat groups first (to which user belongs directly)
        try:
            flat_groups_dns = set(map(force_text, ldap_user.attrs["memberOf"]))
        except KeyError:
            flat_groups_dns = set()
        logger.info("Flat groups DNs for {}: {}".format(username, flat_groups_dns))
        handle_groups(flat_groups_dns)
        from ralph.accounts.management.commands.ldap_sync import get_nested_groups  # noqa

        # handle nested groups
        nested_groups_dns = get_nested_groups()[1].get(username, set())
        logger.info("Nested groups DNs for {}: {}".format(username, nested_groups_dns))
        handle_groups(nested_groups_dns)
        return group_map

    def group_name_from_info(self, group_info):
        """Map ldap group names into ralph names if mapping defined."""
        if self.ldap_groups:
            for dn in group_info[1]["distinguishedname"]:
                mapped = self.ldap_groups.get(dn)
                if mapped:
                    return mapped
        # return original name if mapping not defined
        else:
            return super(MappedGroupOfNamesType, self).group_name_from_info(group_info)
