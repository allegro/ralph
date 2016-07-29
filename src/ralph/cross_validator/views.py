from django.conf import settings
from django.contrib import messages
from django.utils.safestring import mark_safe


class ShowDiffMessageMixin(object):
    diff_message = 'Latest diff between Ralph 2 and Ralph 3:<br>{}'

    # def changeform_view(self, request, object_id, *args, **kwargs):
    #     response = super().changeform_view(
    #         request, object_id, *args, **kwargs
    #     )
    #     if not settings.RALPH2_RALPH3_CROSS_VALIDATION_ENABLED:
    #         return response
    #     from ralph.cross_validator.models import CrossValidationResult
    #     from ralph.cross_validator.admin import get_html_diff
    #     obj = self.get_object(request, object_id)
    #     if not obj:
    #         return response
    #     print(obj.__class__)
    #     last_diff = CrossValidationResult.get_last_diff(obj)
    #     if last_diff and obj and last_diff.created > obj.modified:
    #         if last_diff.errors:
    #             msg = '<ul>'
    #             for error in last_diff.errors:
    #                 msg += '<li>{}</li>'.format(error)
    #             msg += '</ul>'
    #         else:
    #             msg = get_html_diff(last_diff)
    #         messages.info(
    #             request, mark_safe(self.diff_message.format(msg))
    #         )
    #     return response
