# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from ralph.admin.autocomplete import AutocompleteList
from ralph.admin.sites import ralph_site

urlpatterns = [
    url(
        r"^(?P<app>\w+)/(?P<model>\w+)/(?P<field>\w+)/autocomplete$",
        login_required(ralph_site.admin_view(AutocompleteList.as_view())),
        name="autocomplete-list",
    ),
]
