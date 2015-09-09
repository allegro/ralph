# -*- coding: utf-8 -*-
from django.conf.urls import url

from ralph.reports import views

urlpatterns = [
    url(
        r'^category_model_report/?$',
        views.ReportDetail.as_view(),
        name='category_model_report'
    ),
    url(
        r'^category_model__status_report/?$',
        views.ReportWithoutAllModeDetail.as_view(),
        name='category_model__status_report'
    ),
    url(
        r'^manufactured_category_model_report/?$',
        views.ReportDetail.as_view(),
        name='manufactured_category_model_report'
    ),
    url(
        r'^status_model_report/?$',
        views.ReportWithoutAllModeDetail.as_view(),
        name='status_model_report'
    ),
]
