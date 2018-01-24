from ralph.admin.views.extra import RalphDetailView


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        related_objects = {}
        self._add_cloud_hosts(related_objects)
        context['related_objects'] = related_objects

        return context
