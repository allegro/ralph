from django import forms


class CharFormFieldWithAutoStrip(forms.CharField):
    def to_python(self, value):
        return super().to_python(value.strip())

