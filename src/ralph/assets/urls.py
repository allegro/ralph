# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf.urls.defaults import patterns
from django.contrib.auth.decorators import login_required
from django.conf.urls.defaults import url
from django.views.generic import RedirectView

from ralph.assets.views import (
    BackOfficeSearch, DataCenterSearch, BackOfficeAdd, DataCenterAdd
)


urlpatterns = patterns(
    '',
    url(r'^$', RedirectView.as_view(url='/assets/dc/search')),
    url(r'dc/$', RedirectView.as_view(url='/assets/dc/search')),
    url(r'back_office/$', RedirectView.as_view(url='/assets/back_office/search')),

    url(r'dc/search', login_required(DataCenterSearch.as_view())),
    url(r'dc/add', login_required(DataCenterAdd.as_view())),

    url(r'back_office/search', login_required(BackOfficeSearch.as_view())),
    url(r'back_office/add', login_required(BackOfficeAdd.as_view())),
)
