from django.urls import re_path

from ralph.dc_view.views.ui import ServerRoomView, SettingsForAngularView

urlpatterns = [
    re_path(r"^dc_view/?$", ServerRoomView.as_view(), name="dc_view"),
    re_path(
        r"^settings.js$",
        SettingsForAngularView.as_view(),
        name="settings-js",
    ),
]
