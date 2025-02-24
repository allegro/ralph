from django.conf.urls import url

from ralph.attachments.views import ServeAttachment

urlpatterns = [
    url(
        r"^attachment/(?P<id>\d+)-(?P<filename>.+)",
        ServeAttachment.as_view(),
        name="serve_attachment",
    ),
]
