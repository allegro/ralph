# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required
from django.urls import re_path

from ralph.admin.autocomplete import AutocompleteList
from ralph.admin.sites import ralph_site

urlpatterns = [
    re_path(
        r"^(?P<app>\w+)/(?P<model>\w+)/(?P<field>\w+)/autocomplete$",
        login_required(ralph_site.admin_view(AutocompleteList.as_view())),
        name="autocomplete-list",
    ),
]
