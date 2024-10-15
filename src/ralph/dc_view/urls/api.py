from django.conf.urls import url

from ralph.dc_view.views.api import DCAssetsView, SRRacksAPIView

urlpatterns = [
    url(
        r"^rack/(?P<rack_id>\d+)/?$",
        DCAssetsView.as_view(),
    ),
    url(
        r"^server_room/(?P<server_room_id>\d+)/?$",
        SRRacksAPIView.as_view(),
    ),
]
