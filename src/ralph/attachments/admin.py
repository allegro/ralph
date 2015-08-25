import time

from django.conf.urls import url
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils.http import http_date

from ralph.attachments.models import Attachment
from ralph.attachments.views import AttachmentsView


class AttachmentsMixin(object):
    """
    Mixin add new URL to admin for download file.
    """
    def __init__(self, *args, **kwargs):
        self.change_views.append(AttachmentsView)
        super().__init__(*args, **kwargs)

    def get_urls(self):
        urlpatterns = super().get_urls()
        urlpatterns += [
            url(
                r'^attachment/(?P<id>\d+)-(?P<filename>\S+)',
                self.serve_attachment,
                name='get_attachment'
            ),
        ]
        return urlpatterns

    def serve_attachment(self, request, id, filename):
        """
        All attachments are serving by this view because we need full
        control (e.g., permissions, rename).
        """
        # TODO: respect permissions
        obj = get_object_or_404(Attachment, id=id, original_filename=filename)
        fd = open(obj.file.path, 'rb')
        response = FileResponse(fd, content_type=obj.mime_type)
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(obj.original_filename)  # noqa
        http_modified = http_date(time.mktime(obj.modified.timetuple()))
        response['Last-Modified'] = http_modified
        return response
