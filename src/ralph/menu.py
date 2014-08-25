# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.core.exceptions import ImproperlyConfigured

from bob.menu import MenuItem
from ralph.account.models import Perm


class Menu(object):
    module = None

    def __init__(self, request, **kwargs):
        self.request = request
        self.kwargs = kwargs
        profile = self.request.user.get_profile()
        self.has_perm = profile.has_perm

    def generate_menu_items(self, data):
        return [MenuItem(**t) for t in data]

    def get_module(self):
        if not self.module:
            raise ImproperlyConfigured(
                'Menu required definition of \'module\' or an implementation '
                'of \'get_module()\'')

        if not isinstance(self.module, MenuItem):
            raise ImproperlyConfigured(
                'Module must inheritence from \'MenuItem\'')

        return self.module

    def get_active_submodule(self):
        if not self.submodule:
            raise ImproperlyConfigured(
                'Menu required definition of \'submodule\' or an '
                'implementation of \'get_active_submodule()\'')

        if not isinstance(self.submodule, MenuItem):
            raise ImproperlyConfigured(
                'submodule must inheritence from \'MenuItem\'')

        return self.submodule

    def get_submodules(self):
        return []

    def get_sidebar_items(self):
        return {}


class CoreMenu(Menu):
    module = MenuItem(
        'Core',
        name='module_core',
        fugue_icon='fugue-processor',
        view_name='ventures',
    )

    def __init__(self, *args, **kwargs):
        self.venture = None
        self.object = None
        super(CoreMenu, self).__init__(*args, **kwargs)

    def get_submodules(self):
        submodules = [
            MenuItem(
                'Ventures',
                fugue_icon='fugue-store',
                view_name='ventures',
            )
        ]
        if self.has_perm(Perm.read_dc_structure):
            submodules.append(
                MenuItem('Racks', fugue_icon='fugue-building',
                         view_name='racks'))
        if self.has_perm(Perm.read_network_structure):
            submodules.append(
                MenuItem('Networks', fugue_icon='fugue-weather-clouds',
                         view_name='networks'))
        if self.has_perm(Perm.read_device_info_reports):
            submodules.append(
                MenuItem('Reports', fugue_icon='fugue-report',
                         view_name='reports'))
        submodules.append(
            MenuItem('Ralph CLI', fugue_icon='fugue-terminal',
                     href='#beast'))
        submodules.append(
            MenuItem('Quick scan', fugue_icon='fugue-radar',
                     href='#quickscan'))
        submodules.append(
            MenuItem('Search', fugue_icon='fugue-application-search-result',
                     view_name='search', name='search'))
        return submodules

    def get_sidebar_items(self):
        return {}

menu_class = CoreMenu
