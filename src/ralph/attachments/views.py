from django.forms.models import modelformset_factory
from django.http import HttpResponseRedirect

from ralph.admin.views.extra import RalphDetailView
from ralph.attachments.forms import AttachmentForm
from ralph.attachments.models import Attachment, AttachmentItem
from ralph.helpers import add_request_to_form


class AttachmentsView(RalphDetailView):
    icon = 'paperclip'
    name = 'attachment'
    label = 'Attachments'
    url_name = 'attachment'
    template_name = 'attachments/attachments.html'
    extra = 5

    def get_formset(self, request):
        """
        The method returns formset with modified form (with request inside)
        and current attachments assigned to object.
        """
        qs = Attachment.objects.get_attachments_for_object(self.object)
        return modelformset_factory(
            Attachment,
            form=add_request_to_form(AttachmentForm, request),
            fields=('file', 'description'),
            extra=self.extra,
            can_delete=True,
        )(request.POST or None, request.FILES or None, queryset=qs)

    def get(self, request, *args, **kwargs):
        """
        Render formset with data.
        """
        formset = self.get_formset(request)
        return self.render_to_response(self.get_context_data(formset=formset))

    def post(self, request):
        """
        Valid and return response from appropriate method depending on
        the valid result (valid or not).
        """
        formset = self.get_formset(request)
        response = None
        if formset.is_valid():
            response = self.formset_valid(formset)
        else:
            response = self.formset_invalid(formset)
        return response

    def formset_valid(self, formset):
        """
        The method is executed only if formset is valid.
        """
        formset.save()
        AttachmentItem.objects.refresh(
            self.object, formset.new_objects, formset.deleted_objects
        )
        return HttpResponseRedirect('.')

    def formset_invalid(self, formset):
        """
        The method is executed only if formset is invalid.
        """
        return self.render_to_response(
            self.get_context_data(formset=formset)
        )
