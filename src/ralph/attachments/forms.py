from django import forms

from ralph.attachments.models import Attachment
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
        obj.uploaded_by = self._request.user
        file = self.cleaned_data.get('file', None)
        if file and hasattr(file, 'content_type'):
            obj.mime_type = file.content_type
        if commit:
            obj.save()
        return obj
