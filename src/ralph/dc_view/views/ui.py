from django.db.models import Count

from ralph.admin.mixins import RalphTemplateView
from ralph.data_center.models.physical import DataCenter


class ServerRoomView(RalphTemplateView):
    template_name = 'dc_view/server_room_view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['data_centers'] = DataCenter.objects.annotate(
            rooms_count=Count('serverroom')
        ).filter(rooms_count__gt=0)
        context['site_header'] = "Ralph 3"
        return context
