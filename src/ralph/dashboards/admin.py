import json
from itertools import groupby

from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from ralph.admin import RalphAdmin, register
from ralph.admin.mixins import RalphAdminForm
from ralph.dashboards.models import Dashboard, Graph


class GraphForm(RalphAdminForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [
            ct for ct in ContentType.objects.all()
            if getattr(ct.model_class(), '_allow_in_dashboard', False)
        ]

        def keyfunc(x):
            return x.app_label

        data = sorted(choices, key=keyfunc)
        self.fields['model'] = forms.ChoiceField(choices=(
            (k.capitalize(), list(map(lambda x: (x.id, x), g)))
            for k, g in groupby(data, keyfunc)
        ))

        self.initial['params'] = json.dumps(
            self.initial.get('params', {}),
            indent=4,
            sort_keys=True
        )

    def clean_model(self):
        ct_id = self.cleaned_data.get('model')
        return ContentType.objects.get(pk=ct_id)

    def clean_params(self):
        params = self.cleaned_data.get('params', '{}')
        try:
            params_dict = json.loads(params)
        except ValueError as e:
            raise forms.ValidationError(e.msg)
        if not params_dict.get('labels', None):
            raise forms.ValidationError('Please specify `labels` key')
        if not params_dict.get('series', None):
            raise forms.ValidationError('Please specify `series` key')
        return params

    class Meta:
        model = Graph
        fields = [
            'name', 'description', 'model', 'aggregate_type', 'chart_type',
            'params', 'active'
        ]


@register(Graph)
class GraphAdmin(RalphAdmin):
    form = GraphForm
    list_display = ['name', 'description', 'active']


@register(Dashboard)
class DashboardAdmin(RalphAdmin):
    list_display = ['name', 'description', 'active', 'get_link']

    def get_link(self, obj):
        return _('<a href="{}" target="_blank">Dashboard</a>'.format(reverse(
            'dashboard_view', args=(obj.pk,)
        )))
    get_link.short_description = _('Link')
    get_link.allow_tags = True
