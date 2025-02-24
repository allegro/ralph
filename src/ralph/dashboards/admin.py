import json
from itertools import groupby

from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from ralph.admin.decorators import register
from ralph.admin.mixins import RalphAdmin, RalphAdminForm
from ralph.dashboards.models import Dashboard, Graph


class GraphForm(RalphAdminForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [
            ct
            for ct in ContentType.objects.all()
            if getattr(ct.model_class(), "_allow_in_dashboard", False)
        ]

        def keyfunc(x):
            return x.app_label

        data = sorted(choices, key=keyfunc)
        self.fields["model"] = forms.ChoiceField(
            choices=(
                (k.capitalize(), list(map(lambda x: (x.id, x), g)))
                for k, g in groupby(data, keyfunc)
            )
        )

        self.initial["params"] = json.dumps(
            self.initial.get("params", {}), indent=4, sort_keys=True
        )

    def clean_model(self):
        ct_id = self.cleaned_data.get("model")
        return ContentType.objects.get_for_id(id=ct_id)

    def clean_params(self):
        params = self.cleaned_data.get("params", "{}")
        try:
            params_dict = json.loads(params)
        except ValueError as e:
            raise forms.ValidationError(str(e))
        if not params_dict.get("labels", None):
            raise forms.ValidationError("Please specify `labels` key")
        if not params_dict.get("series", None):
            raise forms.ValidationError("Please specify `series` key")
        return params

    class Meta:
        model = Graph
        fields = [
            "name",
            "description",
            "model",
            "aggregate_type",
            "chart_type",
            "params",
            "active",
        ]

    class Media:
        js = ("vendor/js/chartist.js", "js/chartist-plugin-barlabels.js")


@register(Graph)
class GraphAdmin(RalphAdmin):
    form = GraphForm
    list_display = ["name", "description", "active"]
    readonly_fields = ["get_preview"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "description",
                    "model",
                    "aggregate_type",
                    "chart_type",
                    "params",
                    "active",
                    "push_to_statsd",
                )
            },
        ),
        (
            "Preview",
            {
                "fields": ("get_preview",),
            },
        ),
    )

    def get_readonly_fields(self, *args, **kwargs):
        readonly_fields = super().get_readonly_fields(*args, **kwargs)
        allow_push_graphs_data_to_statsd = (
            not settings.ALLOW_PUSH_GRAPHS_DATA_TO_STATSD
            and not settings.COLLECT_METRICS
        )
        if allow_push_graphs_data_to_statsd:
            readonly_fields.append("push_to_statsd")
        return readonly_fields

    def get_preview(self, obj):
        return obj.render(name="preview")

    get_preview.short_description = _("Graph")


@register(Dashboard)
class DashboardAdmin(RalphAdmin):
    list_display = ["name", "description", "active", "get_link"]

    @mark_safe
    def get_link(self, obj):
        return _(
            '<a href="{}" target="_blank">Dashboard</a>'.format(
                reverse("dashboard_view", args=(obj.pk,))
            )
        )

    get_link.short_description = _("Link")
