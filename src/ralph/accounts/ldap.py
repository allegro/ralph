# -*- coding: utf-8 -*-
from dj.choices import Country
from django.conf import settings
from django.dispatch import receiver
from django.utils.encoding import force_text
from django_auth_ldap.backend import LDAPSettings, populate_user
from django_auth_ldap.config import ActiveDirectoryGroupType

# Add default value to LDAPSetting dict. It will be replaced by
# django_auth_ldap with value in settings.py and visible for each
# ldap_user.
LDAPSettings.defaults['GROUP_MAPPING'] = {}


@receiver(populate_user)
def staff_superuser_populate(sender, user, ldap_user, **kwargs):
    user.is_superuser = 'superuser' in ldap_user.group_names
    user.is_staff = 'staff' in ldap_user.group_names
    # only staff users will have access to ralph now,
    # because ralph using django admin panel
    user.is_active = 'staff' in ldap_user.group_names


@receiver(populate_user)
def manager_country_attribute_populate(
    sender, user, ldap_user, **kwargs
):
    try:
        profile_map = settings.AUTH_LDAP_USER_ATTR_MAP
    except AttributeError:
        profile_map = {}
    if 'manager' in profile_map:
        if profile_map['manager'] in ldap_user.attrs:
            manager_ref = force_text(
                ldap_user.attrs[profile_map['manager']][0]
            )
            # CN=John Smith,OU=TOR,OU=Corp-Users,DC=mydomain,DC=internal
            cn = manager_ref.split(',')[0][3:]
            user.manager = cn
    # raw value from LDAP is in profile.country for this reason we assign
    # some correct value
    user.country = None
    if 'country' in profile_map:
        if profile_map['country'] in ldap_user.attrs:
            country = force_text(ldap_user.attrs[profile_map['country']][0])
            # assign None if `country` doesn't exist in Country
            try:
                user.country = Country.id_from_name(country.lower())
            except ValueError:
                user.country = None


class MappedGroupOfNamesType(ActiveDirectoryGroupType):

    """Provide group mappings described in project settings."""

    def _get_group(self, group_dn, ldap_user, group_search):
        base_dn = group_search.base_dn
        group_search.base_dn = force_text(group_dn)
        group = group_search.execute(ldap_user.connection)[0]
        group_search.base_dn = base_dn
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
            group_dns = filter(
                lambda x: force_text(x) in self._ldap_groups, group_dns
            )
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
