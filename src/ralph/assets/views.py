#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.ui.views.common import Base
from bob.menu import MenuItem


class AssetsMixin(Base):
    template_name = "assets/index.html"

    def get(self, *args, **kwargs):
        return super(AssetsMixin, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        return super(AssetsMixin, self).post(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        ret = super(AssetsMixin, self).get_context_data(**kwargs)
        ret.update({
            'sidebar_items': self.get_sidebar_items(),
            'mainmenu_items': self.get_mainmenu_items(),
            'tabs_left': False,
            'section': 'assets',
        })
        return ret

    def get_mainmenu_items(self):
        return[MenuItem(label='Data center',
                fugue_icon='fugue-building',
                href='/assets/dc'),
            MenuItem(label='BackOffice',
                fugue_icon='fugue-printer',
                #fugue_icon='fugue-paper-plane-return',
                href='/assets/back_office'),
        ]


class DataCenterMixin(AssetsMixin):
    def get_mainmenu_items(self):
        return[MenuItem(label='Data center',
                fugue_icon='fugue-building',
                href='/assets/dc'),
            MenuItem(label='BackOffice',
                fugue_icon='fugue-printer',
                #fugue_icon='fugue-paper-plane-return',
                href='/assets/back_office'),
        ]


class BackOfficeMixin(AssetsMixin):
    def get_mainmenu_items(self):
        return[MenuItem(label='Data center',
                fugue_icon='fugue-building',
                href='/assets/dc'),
            MenuItem(label='BackOffice',
                fugue_icon='fugue-printer',
                #fugue_icon='fugue-paper-plane-return',
                href='/assets/back_office'),
        ]


class DataCenterSearch(DataCenterMixin):
    pass


class BackOfficeSearch(BackOfficeMixin):
    pass

