# -*- coding: utf-8 -*-
from django.conf.urls import url

from ralph.admin.autocomplete import AutocompleteList
from ralph.admin.sites import ralph_site

urlpatterns = [
    url(
        r'^(?P<app>\w+)/(?P<model>\w+)/(?P<field>\w+)/autocomplete$',
        ralph_site.admin_view(AutocompleteList.as_view()),
        name='autocomplete-list'
    ),
]
