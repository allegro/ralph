# -*- coding: utf-8 -*-

"""A one-time command that should fix the devices in assets that have no
slot information. We take this info from catalog to fix existing data."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import textwrap
from optparse import make_option

from django.core.management.base import BaseCommand
from django.db import connection, transaction

class Command(BaseCommand):
    """Check for the devices in the database that have no 'slots' set, but the
    data in cataolog suggests, they should. Try to fix this information
    with the use of catalog."""

    help = textwrap.dedent(__doc__).strip()

    option_list = BaseCommand.option_list + (
        make_option(
            '--commit',
            dest='commit',
            action='store_true',
            help="Commit the fix to the database",
        ),
    )

    FIX_QUERY = """
        UPDATE ralph_assets_asset
        LEFT JOIN ralph_assets_deviceinfo
            ON ralph_assets_deviceinfo.id = ralph_assets_asset.device_info_id
        LEFT JOIN discovery_device
            ON ralph_assets_deviceinfo.ralph_device_id = discovery_device.id
        LEFT JOIN discovery_devicemodel
            ON discovery_device.model_id = discovery_devicemodel.id
        LEFT JOIN discovery_devicemodelgroup
            ON discovery_devicemodelgroup.id = discovery_devicemodel.group_id
        SET ralph_assets_asset.slots = discovery_devicemodelgroup.slots
        WHERE ralph_assets_asset.slots = 0 AND
            discovery_devicemodelgroup.slots IS NOT NULL AND
            discovery_devicemodelgroup.slots <> 0;
    """
    COUNT_QUERY = """
        SELECT COUNT(*) FROM ralph_assets_asset
        WHERE ralph_assets_asset.slots <> 0;
    """

    def __init__(self):
        self.cur = connection.cursor()

    def _get_count_with_slots(self):
        """Return the number of currently slotless blade devices."""
        self.cur.execute(self.COUNT_QUERY);
        return self.cur.fetchall()[0][0]

    def handle(self, commit, **kwargs):
        """Perform the query and print out some stats."""
        before_count = self._get_count_with_slots()
        self.cur.execute(self.FIX_QUERY);
        after_count = self._get_count_with_slots()
        fixed_count = after_count - before_count

        print("""
Assets with slots:
Before fix: {before_count}
After_fix: {after_count}
Fixed: {fixed_count}
        """.format(**locals()))
        if commit:
            transaction.commit_unless_managed()
        else:
            print(
                """Use this command with --commit switch
                to commit the fix to database."""
        )
