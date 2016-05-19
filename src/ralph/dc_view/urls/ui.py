from django.conf.urls import url

from ralph.dc_view.views.ui import ServerRoomView

urlpatterns = [
    url(
        r'^dc_view/?$',
        ServerRoomView.as_view(),
        name='dc_view'
    ),
]
