from django.conf.urls import url

from ralph.dc_view.views.api import DCAssetsView, DCRacksAPIView

urlpatterns = [
    url(
        r'^rack/?$',
        DCAssetsView.as_view(),
    ),
    url(
        r'^rack/(?P<rack_id>\d+)/?$',
        DCAssetsView.as_view(),
    ),
    url(
        r'^data_center/(?P<data_center_id>\d+)/?$',
        DCRacksAPIView.as_view(),
    ),
]
