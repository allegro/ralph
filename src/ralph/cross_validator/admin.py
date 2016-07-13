from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.utils.html import mark_safe

from .models import CrossValidationResult, CrossValidationRun

from ralph.admin import RalphAdmin, register


def format_diff(pos, value):
    formatted = ''
    for i, c in enumerate(value):
        if i in pos:
            formatted += '<span style="color:red">{}</span>'.format(c)
        else:
            formatted += c
    return formatted


def get_diff_positions(old, new):
    diff_pos = [
        i for i in range(max(len(new), len(old)))
        if new[i:i + 1] != old[i:i + 1]
    ]
    return diff_pos


def get_html_diff(obj):
    html = ''
    for item, values in obj.diff.items():
        old = str(values['old']) or ''
        new = str(values['new']) or ''
        diff_pos = get_diff_positions(old, new)
        html += """
            <ul><strong>{item}</strong>
            <li>Ralph2: {mono_start}{old}{mono_end}</li>
            <li>Ralph3: {mono_start}{new}{mono_end}</li>
            </ul>
        """.format(
            item=item,
            mono_start='<span style="font-family:monospace">',
            old=format_diff(diff_pos, old),
            new=format_diff(diff_pos, new),
            mono_end='</span>',
        )
    return html


@register(ContentType)
class ContentTypeAdmin(RalphAdmin):
    search_fields = ['model']


@register(CrossValidationRun)
class RunAdmin(RalphAdmin):
    list_display = [
        'created', 'checked_count', 'invalid_count', 'valid_count', 'results'
    ]
    list_display_links = None

    def results(self, run):
        def _get_url(ct_id):
            return '{}?content_type={}&run={}'.format(
                reverse('admin:{}_{}_changelist'.format(
                    CrossValidationResult._meta.app_label,
                    CrossValidationResult._meta.model_name
                )), ct_id, run.id,
            )
        result_qs = CrossValidationResult.objects.filter(
            run=run
        ).values_list(
            'content_type_id', 'content_type__model'
        ).annotate(c=Count('id')).order_by()
        result = """
        <ul>{}</ul>
        """.format(
            ''.join([
                "<li><a href='{}'>{} ({})</a></li>".format(
                    _get_url(ct_id), ct_name, count
                ) for ct_id, ct_name, count in result_qs
            ])
        )
        return result
    results.allow_tags = True


@register(CrossValidationResult)
class ResultAdmin(RalphAdmin):
    list_display = [
        'id', 'get_object_display', 'get_diff_display', 'get_errors_display'
    ]
    list_filter = ['run', 'content_type']
    list_display_links = None
    raw_id_fields = ['content_type', 'run']

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).select_related(
            'content_type'
        )

    def get_diff_display(self, obj):
        if not bool(obj.diff) or bool(obj.errors):
            return mark_safe('-')
        return mark_safe(get_html_diff(obj))
    get_diff_display.short_description = 'Diff'

    def get_errors_display(self, obj):
        html = '<br>'.join(obj.errors)
        return mark_safe(html) or '-'
    get_errors_display.short_description = 'Errors'

    def get_object_display(self, result):
        return '<a href="{}">{} id: {} ({})</a>'.format(
            result.object.get_absolute_url(),
            result.content_type,
            result.object_pk,
            str(result.object)
        )
    get_object_display.allow_tags = True
    get_object_display.short_description = 'Object'
