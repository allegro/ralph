"""Forms for editing a rack's switch columns (RackConfiguration)."""

from django import forms
from django.forms import inlineformset_factory

from ralph.switchports.models import RackConfiguration, RackSwitchConfiguration
from ralph.switchports.rackconfig.switch_resolver import (
    rack_data_center,
    resolve_switch,
)


class RackConfigurationForm(forms.ModelForm):
    class Meta:
        model = RackConfiguration
        fields = ["description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class RackSwitchConfigurationForm(forms.ModelForm):
    """Row form for a single switch column of a rack.

    The ``switch`` FK is entered as a free-text barcode/hostname (resolved the
    same way as the switchport grid) instead of a giant asset dropdown.
    """

    switch_identifier = forms.CharField(
        label="Switch (barcode, hostname or rackNuM)",
        required=False,
        help_text=(
            "Barcode, hostname, or a rack position like "
            "<code>rack12u42</code> (switch at position 42 of the rack whose "
            "name ends with 12, in this rack's data center)."
        ),
    )

    class Meta:
        model = RackSwitchConfiguration
        fields = ["label", "backend_validation"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.switch_id:
            switch = self.instance.switch
            self.fields["switch_identifier"].initial = (
                switch.barcode or switch.hostname
            )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("DELETE"):
            return cleaned_data
        label = (cleaned_data.get("label") or "").strip()
        identifier = (cleaned_data.get("switch_identifier") or "").strip()
        # Untouched blank extra row - nothing to validate or save.
        if not label and not identifier:
            return cleaned_data
        rack_config = getattr(self.instance, "rack_configuration", None)
        dc = rack_data_center(getattr(rack_config, "rack", None))
        switch = resolve_switch(identifier, dc)
        if switch is None:
            self.add_error(
                "switch_identifier",
                "Unknown switch '{}'.".format(identifier)
                if identifier
                else "This field is required.",
            )
        else:
            self.instance.switch = switch
        return cleaned_data


RackSwitchConfigurationFormSet = inlineformset_factory(
    RackConfiguration,
    RackSwitchConfiguration,
    form=RackSwitchConfigurationForm,
    extra=1,
    can_delete=True,
)
