# -*- coding: utf-8 -*-
from django.urls import re_path

from ralph.reports import views

urlpatterns = [
    re_path(
        r"^category_model_report/?$",
        views.CategoryModelReport.as_view(),
        name="category_model_report",
    ),
    re_path(
        r"^category_model__status_report/?$",
        views.CategoryModelStatusReport.as_view(),
        name="category_model__status_report",
    ),
    re_path(
        r"^manufactured_category_model_report/?$",
        views.ManufacturerCategoryModelReport.as_view(),
        name="manufactured_category_model_report",
    ),
    re_path(
        r"^status_model_report/?$",
        views.StatusModelReport.as_view(),
        name="status_model_report",
    ),
    re_path(
        r"^asset_relations/?$",
        views.AssetRelationsReport.as_view(),
        name="asset-relations",
    ),
    re_path(
        r"^licence_relations/?$",
        views.LicenceRelationsReport.as_view(),
        name="licence-relations",
    ),
    re_path(
        r"^failures_report/?$", views.FailureReport.as_view(), name="failures-report"
    ),
    re_path(
        r"^supports_report/?$",
        views.AssetSupportsReport.as_view(),
        name="assets-supports",
    ),
]
