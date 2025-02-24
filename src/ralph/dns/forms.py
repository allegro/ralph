# -*- coding: utf-8 -*-
from dj.choices import Choices
from django import forms
from django.utils.translation import ugettext_lazy as _


class RecordType(Choices):
    _ = Choices.Choice

    a = _("A")
    txt = _("TXT")
    cname = _("CNAME")


class DNSRecordForm(forms.Form):
    pk = forms.IntegerField(label="", widget=forms.HiddenInput(), required=False)
    name = forms.CharField(
        label=_("Name"),
        max_length=255,
        help_text=_(
            "Actual name of a record. Must not end in a '.' and be"
            " fully qualified - it is not relative to the name of the"
            " domain!"
        ),
    )
    type = forms.ChoiceField(
        label=_("Record type"),
        choices=RecordType(),
    )
    content = forms.CharField(
        label=_("Content"),
        max_length=255,
        help_text=_(
            "The 'right hand side' of a DNS record. For an A"
            " record, this is the IP address"
        ),
        widget=forms.TextInput(attrs={"style": "width:300px;"}),
    )
    ptr = forms.BooleanField(
        label=_("PTR"),
        initial=False,
        required=False,
        widget=forms.CheckboxInput(attrs={"disabled": True}),
    )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("ptr", False) and cleaned_data.get("type", None) != str(
            RecordType.a.id
        ):
            raise forms.ValidationError(_("Only A type record can be PTR"))
