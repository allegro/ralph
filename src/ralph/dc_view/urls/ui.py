from django.conf.urls import url

from ralph.dc_view.views.ui import ServerRoomView, SettingsForAngularView

urlpatterns = [
    url(r"^dc_view/?$", ServerRoomView.as_view(), name="dc_view"),
    url(
        r"^settings.js$",
        SettingsForAngularView.as_view(),
        name="settings-js",
    ),
]
