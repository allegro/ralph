from django import forms

from ralph.admin.helpers import get_content_type_for_model
from ralph.attachments.models import Attachment, AttachmentItem
from ralph.lib.mixins.forms import RequestModelForm


class ChangeAttachmentWidget(forms.ClearableFileInput):
    template_with_initial = (
        '<div>%(input_text)s: %(input)s</div>'
    )


class AttachmentForm(RequestModelForm):

    class Meta:
        fields = ['file', 'description']
        model = Attachment
        widgets = {
            'file': ChangeAttachmentWidget(),
            'description': forms.Textarea(attrs={'rows': 2, 'cols': 30}),
        }

    def save(self, commit=True):
        """
        Overrided standard save method. Saving object with attributes:
            * uploaded_by - user from request,
            * mime_type - uploaded file's content type.
        """
        obj = super().save(commit=False)
        md5 = Attachment.get_md5_sum(obj.file)
        attachment = Attachment.objects.filter(md5=md5)
        if obj.pk:
            attachment = attachment.exclude(pk=obj.pk)
        attachment = attachment.first()
        # _parent_object is an object to which it is assigned Attachment.
        # _parent_object is set in attachment.views.AttachmentsView
        #  get_formset method.
        if attachment:
            content_type = get_content_type_for_model(
                self._parent_object._meta.model
            )
            if not AttachmentItem.objects.filter(
                content_type=content_type,
                object_id=self._parent_object.pk,
                attachment__md5=md5
            ).exists():
                AttachmentItem.objects.attach(
                    self._parent_object.pk, content_type, [attachment]
                )
                return None
            return
        obj.md5 = md5
        obj.uploaded_by = self._request.user
        file = self.cleaned_data.get('file', None)
        if file and hasattr(file, 'content_type'):
            obj.mime_type = file.content_type
        obj.save()
        return obj
