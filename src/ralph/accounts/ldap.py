# -*- coding: utf-8 -*-
import logging

from dj.choices import Country
from django.conf import settings
from django.contrib.auth.models import Group
from django.dispatch import receiver
from django.utils.encoding import force_text
from django_auth_ldap.backend import _LDAPUser, LDAPSettings, populate_user

logger = logging.getLogger(__name__)

# Add default value to LDAPSetting dict. It will be replaced by
# django_auth_ldap with value in settings.py and visible for each
# ldap_user.
LDAPSettings.defaults["GROUP_MAPPING"] = {}


@receiver(populate_user)
def staff_superuser_populate(sender, user, ldap_user, **kwargs):
    user.is_superuser = "superuser" in ldap_user.group_names
    # only staff users will have access to ralph now,
    # because ralph using django admin panel
    user.is_staff = "active" in ldap_user.group_names
    user.is_active = "active" in ldap_user.group_names


def mirror_groups(self):
    """
    Mirror groups from LDAP, but keep groups not mapped from LDAP assigned to
    user.
    """
    target_group_names = frozenset(self._get_groups().get_group_names())
    # the only difference comparing to original django_auth_ldap:
    if getattr(settings, "AUTH_LDAP_KEEP_NON_LDAP_GROUPS", False):
        # list of groups names mapped from LDAP
        LDAP_GROUPS_NAMES = list(
            getattr(settings, "AUTH_LDAP_GROUP_MAPPING", {}).values()
        ) + list(getattr(settings, "AUTH_LDAP_NESTED_GROUPS", {}).values())
        # include groups not mapped from LDAP into target groups names
        non_ad_groups = list(
            self._user.groups.exclude(name__in=LDAP_GROUPS_NAMES).values_list(
                "name", flat=True
            )
        )
        target_group_names = frozenset(list(target_group_names) + non_ad_groups)
    logger.info(
        "Target groups for user {}: {}".format(
            self._user, ", ".join(target_group_names)
        )
    )
    current_group_names = frozenset(
        self._user.groups.values_list("name", flat=True).iterator()
    )
    if target_group_names != current_group_names:
        logger.info(
            "Modifing user groups: current = {}, target = {}".format(
                ", ".join(current_group_names), ", ".join(target_group_names)
            )
        )
        existing_groups = list(
            Group.objects.filter(name__in=target_group_names).iterator()
        )
        existing_group_names = frozenset(group.name for group in existing_groups)

        new_groups = [
            Group.objects.get_or_create(name=name)[0]
            for name in target_group_names
            if name not in existing_group_names
        ]

        self._user.groups.set(existing_groups + new_groups)


_LDAPUser._mirror_groups_original = _LDAPUser._mirror_groups
_LDAPUser._mirror_groups = mirror_groups


@receiver(populate_user)
def manager_country_attribute_populate(sender, user, ldap_user, **kwargs):
    try:
        profile_map = settings.AUTH_LDAP_USER_ATTR_MAP
    except AttributeError:
        profile_map = {}
    if "manager" in profile_map:
        if profile_map["manager"] in ldap_user.attrs:
            manager_ref = force_text(ldap_user.attrs[profile_map["manager"]][0])
            # CN=John Smith,OU=TOR,OU=Corp-Users,DC=mydomain,DC=internal
            cn = manager_ref.split(",")[0][3:]
            user.manager = cn
    # raw value from LDAP is in profile.country for this reason we assign
    # some correct value
    user.country = None
    if "country" in profile_map:
        if profile_map["country"] in ldap_user.attrs:
            country = force_text(ldap_user.attrs[profile_map["country"]][0])
            # assign None if `country` doesn't exist in Country
            try:
                user.country = Country.id_from_name(country.lower())
            except ValueError:
                user.country = None
