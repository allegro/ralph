from django.urls import re_path

from ralph.attachments.views import ServeAttachment

urlpatterns = [
    re_path(
        r"^attachment/(?P<id>\d+)-(?P<filename>.+)",
        ServeAttachment.as_view(),
        name="serve_attachment",
    ),
]
