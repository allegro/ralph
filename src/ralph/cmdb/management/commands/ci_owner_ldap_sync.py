# -*- coding: utf-8 -*-
"""Synchronise CI owners with LDAP usernames"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import textwrap

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.paginator import Paginator
import ldap
import unidecode

from ralph.cmdb.models_ci import CIOwner
from ralph.util.ldap import get_ldap


def d(value):
    """Strip diacriticals and convert to 8-bit."""
    return unidecode.unidecode(value).encode('ascii')


class Command(BaseCommand):
    """Search LDAP for first/last names of CI Owners and fill the ldap_name
    fields for them."""

    help = textwrap.dedent(__doc__).strip()

    def handle(self, *args, **kwargs):
        conn = get_ldap()
        owner_pages = Paginator(CIOwner.objects.all(), 100)
        print("Found {} CIOwners.".format(owner_pages.count))
        for i in owner_pages.page_range:
            page = owner_pages.page(i)
            for ci_owner in page:
                filter_ = d(ldap.filter.filter_format(
                    '(&(givenName=%s)(sn=%s))',
                    (
                        ci_owner.first_name,
                        ci_owner.last_name,
                    ),
                ))
                result = conn.search_s(
                    settings.AUTH_LDAP_USER_SEARCH_BASE,
                    ldap.SCOPE_SUBTREE,
                    filter_,
                    attrlist=[d('sAMAccountName')],
                )
                if not result:
                    print('No LDAP data found for {}'.format(ci_owner))
                    continue
                if len(result) > 1:
                    print(
                        'Multiple LDAP records found for {}'.format(ci_owner)
                    )
                    continue
                dn, data = result[0]
                account_name = data.get('sAMAccountName')
                if account_name is not None:
                    ci_owner.sAMAccountName = account_name[0]
                    ci_owner.save()
            print('Chunk {} of {} done.'.format(i, owner_pages.page_range))
