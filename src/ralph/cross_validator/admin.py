from django.utils.html import format_html

from ralph.admin import RalphAdmin, register
from .models import Run, Result


def format_diff(pos, value):
    formatted = ''
    for i, c in enumerate(value):
        if i in pos:
            formatted += '<span style="color:red">{}</span>'.format(c)
        else:
            formatted += c
    return formatted

@register(Run)
class RunAdmin(RalphAdmin):
    list_display = ['created', 'checked_count', 'invalid_count', 'valid_count']


@register(Result)
class ResultAdmin(RalphAdmin):
    list_display = ['get_object_display', 'get_result_display', 'get_errors_display']

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).select_related('content_type')

    def get_result_display(self, obj):
        if not bool(obj.result):
            return format_html('-')
        html = ''
        for item, values in obj.result.items():
            old = values['old'] or ''
            new = values['new'] or ''
            diff_pos = [
                i for i in range(min(len(new), len(old))) if new[i] != old[i]
            ]
            html += '<ul><strong>{}</strong></ul><li style="font-family:monospace">{}</li><li style="font-family:monospace">{}</li><br>'.format(
                item, format_diff(diff_pos, old), format_diff(diff_pos, new)
            )
        return format_html(html)
    get_result_display.short_description = 'Diff ({key}: {ralph2} - {ralph3})'

    def get_errors_display(self, obj):
        if not bool(obj.errors):
            return '-'
        html = ''
        for item in obj.errors:
            html += '{}<br>'.format(
                item
            )
        return format_html(html)

    def get_object_display(self, obj):
        return '{} id: {}'.format(obj.content_type, obj.object_pk)
