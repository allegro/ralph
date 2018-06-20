from django.contrib.contenttypes.models import ContentType

from ralph.admin.views.extra import RalphDetailView
from ralph.virtual.models import VirtualServer


class RelationsView(RalphDetailView):
    icon = 'shekel'
    label = 'Relations'
    name = 'relations'
    url_name = 'relations'
    template_name = 'data_center/datacenterasset/relations.html'

    def _add_cloud_hosts(self, related_objects):
        cloud_hosts = list(self.object.cloudhost_set.all())

        if cloud_hosts:
            related_objects['cloud_hosts'] = cloud_hosts

    def _add_virtual_hosts(self, related_objects):
        virtual_server = ContentType.objects.get_for_model(VirtualServer)
        virtual_hosts = list(
            self.object.children.filter(content_type=virtual_server)
        )

        if virtual_hosts:
            related_objects['virtual_hosts'] = virtual_hosts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        related_objects = {}
        self._add_cloud_hosts(related_objects)
        self._add_virtual_hosts(related_objects)
        context['related_objects'] = related_objects

        return context
