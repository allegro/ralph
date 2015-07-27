from ralph.admin.mixins import RalphTemplateView
from ralph.data_center.models.physical import DataCenter


class DataCenterView(RalphTemplateView):

    template_name = 'dc_view/data_center_view.html'

    def get_context_data(self, **kwargs):
        context = super(DataCenterView, self).get_context_data(**kwargs)
        context['data_centers'] = DataCenter.objects.all()
        context['site_header'] = "Ralph 3"
        return context
