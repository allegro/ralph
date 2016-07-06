from django.contrib import messages
from django.utils.safestring import mark_safe

from ralph.cross_validator.admin import get_html_diff
from ralph.cross_validator.models import CrossValidationResult


class ShowDiffMessageMixin(object):
    diff_message = 'Latest diff between Ralph 2 and Ralph 3:<br>{}'

    def changeform_view(self, request, object_id, *args, **kwargs):
        obj = self.get_object(request, object_id)
        last_diff = CrossValidationResult.get_last_diff(obj)
        if last_diff:
            if last_diff.errors:
                msg = '<ul>'
                for error in last_diff.errors:
                    msg += '<li>{}</li>'.format(error)
                msg += '</ul>'
            else:
                msg = get_html_diff(last_diff)
            messages.info(request, mark_safe(self.diff_message.format(msg)))
        return super().changeform_view(request, object_id, *args, **kwargs)
