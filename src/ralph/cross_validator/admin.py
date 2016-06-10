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
    list_display = ['get_object_display', 'get_diff_display', 'get_errors_display']

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).select_related('content_type')

    def get_diff_display(self, obj):
        if not bool(obj.diff):
            return format_html('-')
        html = ''
        for item, values in obj.diff.items():
            old = str(values['old']) or ''
            new = str(values['new']) or ''
            diff_pos = [
                i for i in range(min(len(new), len(old))) if new[i] != old[i]
            ]
            if len(diff_pos) >= 1 and len(diff_pos) <= 4:
                html += '<ul><strong>{}</strong></ul><li style="font-family:monospace">{}</li><li style="font-family:monospace">{}</li>'.format(  # noqa
                    item, format_diff(diff_pos, old), format_diff(diff_pos, new)
                )
            else:
                html += '<ul><strong>{}</strong></ul><li>{}</li><li>{}</li>'.format(  # noqa
                    item, old, new
                )
        return format_html(html)
    get_diff_display.short_description = 'Diff'

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
