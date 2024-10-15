import json

from django.conf import settings
from django.db.models import Count

from ralph.admin.mixins import RalphTemplateView
from ralph.data_center.models.physical import DataCenter


class ServerRoomView(RalphTemplateView):
    template_name = "dc_view/server_room_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["data_centers"] = DataCenter.objects.annotate(
            rooms_count=Count("serverroom")
        ).filter(rooms_count__gt=0)
        context["site_header"] = "Ralph 3"
        return context


class SettingsForAngularView(RalphTemplateView):
    content_type = "application/javascript"
    template_name = "dc_view/settings_for_angular.js"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["settings"] = json.dumps(
            {
                "RACK_LISTING_NUMBERING_TOP_TO_BOTTOM": settings.RACK_LISTING_NUMBERING_TOP_TO_BOTTOM,  # noqa
            }
        )
        return context
