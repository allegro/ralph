from django import forms


class CharFormFieldWithAutoStrip(forms.CharField):
    def to_python(self, value):
        try:
            return super().to_python(value.strip())
        except AttributeError:
            return super().to_python(value)
