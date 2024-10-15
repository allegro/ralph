# -*- coding: utf-8 -*-
from django.core.management import call_command
from django.test import TestCase


class RalphMenuTest(TestCase):
    def test_menu_resync(self):
        call_command("sitetree_resync_apps")
