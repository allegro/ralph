from django.conf.urls import url

from ralph.dc_view.views.ui import DataCenterView

urlpatterns = [
    url(
        r'^dc_view/?$',
        DataCenterView.as_view(),
        name='dc_view'
    ),
]
