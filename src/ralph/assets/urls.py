# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf.urls.defaults import patterns, url
from django.contrib.auth.decorators import login_required
from django.views.generic import RedirectView

from ralph.assets.views import (
    EditDeviceAsset, EditPartAsset, BackOfficeSearch, DataCenterSearch,
    BackOfficeAddDevice, BackOfficeAddPart, DataCenterAddDevice,
    DataCenterAddPart)


urlpatterns = patterns(
    '',
    url(r'^$', RedirectView.as_view(url='/assets/dc/search')),
    url(r'dc/$', RedirectView.as_view(url='/assets/dc/search')),
    url(r'back_office/$',
        RedirectView.as_view(url='/assets/back_office/search')),

    url(r'dc/search', login_required(DataCenterSearch.as_view())),
    url(r'dc/add/device/',
        login_required(DataCenterAddDevice.as_view())),
    url(r'dc/add/part/',
        login_required(DataCenterAddPart.as_view())),

    url(r'back_office/search', login_required(BackOfficeSearch.as_view())),
    url(r'back_office/add/device/',
        login_required(BackOfficeAddDevice.as_view())),
    url(r'back_office/add/part/',
        login_required(BackOfficeAddPart.as_view())),

    url(r'^device/edit/(?P<asset_id>[0-9]+)/$',
        login_required(EditDeviceAsset.as_view())),
    url(r'^part/edit/(?P<asset_id>[0-9]+)/$',
        login_required(EditPartAsset.as_view())),
)
