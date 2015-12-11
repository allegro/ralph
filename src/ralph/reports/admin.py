from ralph.admin import RalphAdmin, RalphTabularInline, register
from ralph.reports.forms import ReportTemplateFormset
from ralph.reports.models import Report, ReportLanguage, ReportTemplate


class ReportTemplateInline(RalphTabularInline):
    model = ReportTemplate
    formset = ReportTemplateFormset
    extra = 0


@register(ReportLanguage)
class ReportLanguage(RalphAdmin):
    list_display = ['name', 'default']


@register(Report)
class ReportAdmin(RalphAdmin):
    search_fields = ('name',)
    list_display = ('name', )
    inlines = [
        ReportTemplateInline,
    ]
