from ralph.admin.views.extra import RalphDetailView


class RelationsView(RalphDetailView):
    icon = 'shekel'
    label = 'Relations'
    name = 'relations'
    url_name = 'relations'
    template_name = 'data_center/datacenterasset/relations.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        related_objects = {}

        if self.object.cloudhost_set.exists():
            related_objects['cloud_hosts'] = [
                i for i in self.object.cloudhost_set.all()
            ]

        context['related_objects'] = related_objects

        return context
