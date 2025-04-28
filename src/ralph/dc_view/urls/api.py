from django.urls import re_path

from ralph.dc_view.views.api import DCAssetsView, SRRacksAPIView

urlpatterns = [
    re_path(
        r"^rack/(?P<rack_id>\d+)/?$",
        DCAssetsView.as_view(),
    ),
    re_path(
        r"^server_room/(?P<server_room_id>\d+)/?$",
        SRRacksAPIView.as_view(),
    ),
]
