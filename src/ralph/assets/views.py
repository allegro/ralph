# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from bob.menu import MenuItem, MenuHeader

from ralph.ui.views.common import Base


class AssetsMixin(Base):
    template_name = "assets/base.html"

    def get(self, *args, **kwargs):
        return super(AssetsMixin, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        return super(AssetsMixin, self).post(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        ret = super(AssetsMixin, self).get_context_data(**kwargs)
        ret.update({
            'sidebar_items': self.get_sidebar_items(),
            'mainmenu_items': self.get_mainmenu_items(),
            'section': 'assets',
            'sidebar_selected': self.sidebar_selected,
            'section': self.mainmenu_selected,
        })

        return ret

    def get_mainmenu_items(self):
        return[MenuItem(label='Data center',
                        name='dc',
                        fugue_icon='fugue-building',
                        href='/assets/dc'),
               MenuItem(label='BackOffice',
                        fugue_icon='fugue-printer',
                        name='back_office',
                        href='/assets/back_office'),
               ]


class DataCenterMixin(AssetsMixin):
    mainmenu_selected = 'dc'

    def get_sidebar_items(self):
        items = (
            ('/assets/dc/add', 'Add', 'fugue-block--plus'),
            ('/assets/dc/search', 'Search', 'fugue-magnifier'),
        )
        sidebar_menu = (
            [MenuHeader('Data center actions')] +
            [MenuItem(
             label=t[1],
             fugue_icon=t[2],
             href=t[0]
             ) for t in items]
        )
        return sidebar_menu


class BackOfficeMixin(AssetsMixin):
    mainmenu_selected = 'back_office'

    def get_sidebar_items(self):
        items = (
                ('/assets/back_office/add', 'Add', 'fugue-block--plus'),
                ('/assets/back_office/search', 'Search', 'fugue-magnifier'),
        )
        sidebar_menu = (
            [MenuHeader('Back office actions')] +
            [MenuItem(
                label=t[1],
                fugue_icon=t[2],
                href=t[0]
            ) for t in items]
        )
        return sidebar_menu


class DataCenterSearch(DataCenterMixin):
    sidebar_selected = 'search'


class DataCenterAdd(DataCenterMixin):
    sidebar_selected = 'add'


class BackOfficeSearch(BackOfficeMixin):
    sidebar_selected = 'search'


class BackOfficeAdd(BackOfficeMixin):
    sidebar_selected = 'add'

