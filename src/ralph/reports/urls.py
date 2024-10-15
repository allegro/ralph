# -*- coding: utf-8 -*-
from django.conf.urls import url

from ralph.reports import views

urlpatterns = [
    url(
        r"^category_model_report/?$",
        views.CategoryModelReport.as_view(),
        name="category_model_report",
    ),
    url(
        r"^category_model__status_report/?$",
        views.CategoryModelStatusReport.as_view(),
        name="category_model__status_report",
    ),
    url(
        r"^manufactured_category_model_report/?$",
        views.ManufacturerCategoryModelReport.as_view(),
        name="manufactured_category_model_report",
    ),
    url(
        r"^status_model_report/?$",
        views.StatusModelReport.as_view(),
        name="status_model_report",
    ),
    url(
        r"^asset_relations/?$",
        views.AssetRelationsReport.as_view(),
        name="asset-relations",
    ),
    url(
        r"^licence_relations/?$",
        views.LicenceRelationsReport.as_view(),
        name="licence-relations",
    ),
    url(r"^failures_report/?$", views.FailureReport.as_view(), name="failures-report"),
    url(
        r"^supports_report/?$",
        views.AssetSupportsReport.as_view(),
        name="assets-supports",
    ),
]
