import logging

from django import forms
from django.contrib import messages
from django.db import transaction
from django.forms import inlineformset_factory
from django.http import HttpResponseRedirect, JsonResponse
from django.utils.functional import cached_property

from ralph.admin.views.extra import RalphDetailView
from ralph.data_center.models import DataCenterAsset
from ralph.lib.external_services import InternalService
from ralph.switchports import connections
from ralph.switchports.models import (
    BackendValidationResult,
    Port,
    RackConfiguration,
    RackSwitchConfiguration,
    RackSwitchConfigurationOverride,
    RefreshJobStatus,
    SwitchportRefreshJob,
    ValidationStatus,
)
from ralph.switchports.presentation import build_validation_context
from ralph.switchports.rack_configuration import _parse
from ralph.switchports.validation import refresh_validation_for_rack  # noqa: F401

logger = logging.getLogger(__name__)


def _port_label_for_switch(port_number_str):
    """Convert user-entered port number to switch port label.

    If the value already contains '/', treat it as a full label.
    Otherwise, format it as '0/0/{number}'.
    """
    port_number_str = port_number_str.strip()
    if "/" in port_number_str:
        return port_number_str
    return f"0/0/{port_number_str}"


def _resolve_switch(identifier, dc=None):
    """Resolve a user-entered switch identifier.

    Accepts a barcode, a hostname, or a ``rack{rack_number}u{position}``
    position string resolved within ``dc`` the same way as
    ``ralph.switchports.rack_configuration._parse`` (e.g. ``rack12u42`` is the
    asset at position 42 of the rack whose name ends with ``12``). The position
    format is only tried when a data center context (``dc``) is available.
    Returns the matching DataCenterAsset or None.
    """
    identifier = identifier.strip()
    if not identifier:
        return None
    try:
        return DataCenterAsset.objects.get(barcode=identifier)
    except DataCenterAsset.DoesNotExist:
        pass
    try:
        return DataCenterAsset.objects.get(hostname=identifier)
    except DataCenterAsset.DoesNotExist:
        pass
    if dc is not None:
        try:
            return _parse(identifier, dc)
        except ValueError:
            return None
    return None


def _rack_data_center(rack):
    """Best-effort data center for a rack (may be None if not placed)."""
    server_room = getattr(rack, "server_room", None)
    return getattr(server_room, "data_center", None)


class RackSwitchportGridView(RalphDetailView):
    icon = "th"
    label = "Switchport Grid"
    name = "switchport_grid"
    url_name = "switchport-grid"
    template_name = "switchports/rackconfiguration/switchport_grid.html"

    @cached_property
    def rack_configuration(self):
        """The RackConfiguration for the rack this tab is rendered for.

        The view is attached to the ``Rack`` admin, so ``self.object`` is a
        ``Rack``. Every rack is expected to have a configuration (created on
        rack creation / by the backfill migration), but we ``get_or_create`` as
        a safety net so the grid never crashes for a rack missing its config.
        """
        rack_config, _ = RackConfiguration.objects.get_or_create(rack=self.object)
        return rack_config

    def _get_rack_assets(self):
        """Get all DataCenterAssets in this rack, ordered by position."""
        return (
            DataCenterAsset.objects.filter(rack=self.object)
            .select_related("model", "model__category")
            .order_by("-position", "slot_no", "hostname")
        )

    def _get_switch_configs(self):
        """Get all RackSwitchConfigurations for this rack, ordered by label."""
        return (
            self.rack_configuration.switches.select_related("switch")
            .order_by("label")
        )

    def _build_override_map(self, switch_configs):
        """Map (asset_id, switch_config_id) -> override switch (DataCenterAsset)."""
        sc_ids = [sc.id for sc in switch_configs]
        override_map = {}
        if not sc_ids:
            return override_map
        overrides = RackSwitchConfigurationOverride.objects.filter(
            rack_switch_configuration_id__in=sc_ids
        ).select_related("switch")
        for override in overrides:
            override_map[
                (override.data_center_asset_id, override.rack_switch_configuration_id)
            ] = override.switch
        return override_map

    def _effective_switch(self, sc, asset_id, override_map):
        """The switch an asset connects to for a column (override or default)."""
        return override_map.get((asset_id, sc.id)) or sc.switch

    def _build_connection_map(self, assets, switch_configs):
        """Build a map of (asset_id, switch_config_id) -> port info.

        Matches an asset's port to a column by label, then records the switch
        port it is connected to and which switch that actually is (which may be
        an override switch rather than the column default).
        """
        label_to_sc = {sc.label: sc for sc in switch_configs}
        asset_ids = [a.id for a in assets]

        if not asset_ids or not label_to_sc:
            return {}

        asset_ports = (
            Port.objects.filter(
                data_center_asset_id__in=asset_ids,
                label__in=list(label_to_sc.keys()),
            )
            .select_related(
                "connectionmember__connection",
            )
            .prefetch_related(
                "connectionmember__connection__members__port__data_center_asset",
            )
        )

        connection_map = {}
        for port in asset_ports:
            sc = label_to_sc.get(port.label)
            if sc is None:
                continue
            conn_member = getattr(port, "connectionmember", None)
            if not conn_member:
                continue
            connection = conn_member.connection
            for member in connection.members.all():
                if member.port_id == port.id:
                    continue
                remote_port = member.port
                remote_asset = remote_port.data_center_asset
                # Only treat the remote as a switch cell if it is not another
                # server in this rack's asset set (heuristic: it is a switch if
                # it differs from the local asset).
                if remote_asset.id == port.data_center_asset_id:
                    continue
                connection_map[(port.data_center_asset_id, sc.id)] = {
                    "switch_port_label": remote_port.label,
                    "asset_port_label": port.label,
                    "actual_switch_id": remote_asset.id,
                }
        return connection_map

    def _build_validation_map(self, switch_configs):
        """Build a map of (switch_id, port_label) -> BackendValidationResult.

        Also returns per-switch status (SWITCH_NOT_FOUND if the sentinel exists).
        """
        results = BackendValidationResult.objects.filter(
            rack_configuration=self.rack_configuration,
        ).select_related("remote_asset")

        validation_map = {}
        switch_status = {}
        for result in results:
            if result.port_label == "__switch__":
                switch_status[result.switch_id] = result.status
            else:
                validation_map[(result.switch_id, result.port_label)] = result

        return validation_map, switch_status

    def _build_client_validation(self, switch_configs, validation_map, switch_status):
        """Serialize default-switch validation for instant, client-side checks.

        Only default (non-override) switches are included: the grid preloads
        every validated port so typing a port number gives immediate feedback
        without any AJAX. Overrides are intentionally excluded.
        """
        client = {}
        for sc in switch_configs:
            if not sc.backend_validation:
                continue
            ports = {}
            for (switch_id, port_label), vr in validation_map.items():
                if switch_id != sc.switch_id:
                    continue
                ports[port_label] = {
                    "status": vr.status,
                    "remote_asset_id": vr.remote_asset_id,
                    "remote_hostname": vr.remote_hostname,
                }
            client[str(sc.id)] = {
                "switch_not_found": sc.switch_id in switch_status,
                "ports": ports,
            }
        return client

    def _latest_refresh_job(self):
        return (
            SwitchportRefreshJob.objects.filter(rack_configuration=self.rack_configuration)
            .order_by("-created")
            .first()
        )

    def get(self, request, *args, **kwargs):
        # Lightweight JSON status endpoint for the in-progress badge polling.
        if request.GET.get("refresh_status"):
            return self._refresh_status_json()
        return super().get(request, *args, **kwargs)

    def _refresh_status_json(self):
        job = self._latest_refresh_job()
        if job is None:
            return JsonResponse({"status": None})
        return JsonResponse(
            {
                "status": job.status,
                "is_running": job.is_running,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "finished_at": (
                    job.finished_at.isoformat() if job.finished_at else None
                ),
                "summary": job.summary,
                "error": job.error,
            }
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assets = list(self._get_rack_assets())
        switch_configs = list(self._get_switch_configs())
        override_map = self._build_override_map(switch_configs)
        connection_map = self._build_connection_map(assets, switch_configs)
        validation_map, switch_status = self._build_validation_map(switch_configs)

        # Check if we have any validation results at all
        has_validation = bool(validation_map) or bool(switch_status)

        # Get last refresh time
        last_refresh = None
        if has_validation:
            last_result = (
                BackendValidationResult.objects.filter(rack_configuration=self.rack_configuration)
                .order_by("-modified")
                .first()
            )
            if last_result:
                last_refresh = last_result.modified

        rows = []
        for asset in assets:
            cells = []
            for sc in switch_configs:
                effective_switch = self._effective_switch(sc, asset.id, override_map)
                override_switch = override_map.get((asset.id, sc.id))
                conn_info = connection_map.get((asset.id, sc.id))
                if conn_info:
                    switch_port_label = conn_info["switch_port_label"]
                    display_value = switch_port_label
                    if switch_port_label.startswith("0/0/"):
                        display_value = switch_port_label[4:]
                else:
                    switch_port_label = None
                    display_value = ""

                # Validation for this cell (keyed by the effective switch)
                validation = None
                if not sc.backend_validation:
                    # Backend validation disabled: no netmaker column.
                    pass
                elif switch_port_label and effective_switch.id in switch_status:
                    validation = {
                        "status": ValidationStatus.SWITCH_NOT_FOUND,
                        "css_class": "validation-error",
                        "label": "SWITCH N/F",
                    }
                elif switch_port_label:
                    vr = validation_map.get((effective_switch.id, switch_port_label))
                    if vr is not None:
                        validation = build_validation_context(
                            vr, expected_asset_id=asset.id
                        )
                    elif has_validation:
                        validation = {
                            "status": ValidationStatus.PORT_NOT_FOUND,
                            "css_class": "validation-warning",
                            "label": "PORT N/F",
                        }

                cells.append(
                    {
                        "switch_config": sc,
                        "value": display_value,
                        "field_name": f"port_{asset.id}_{sc.id}",
                        "override_field_name": f"override_{asset.id}_{sc.id}",
                        "override_value": (
                            override_switch.barcode or override_switch.hostname
                            if override_switch
                            else ""
                        ),
                        "is_override": bool(override_switch),
                        "validation": validation,
                    }
                )
            rows.append({"asset": asset, "cells": cells})

        context["switch_configs"] = switch_configs
        context["switch_status"] = switch_status
        context["rows"] = rows
        context["has_validation"] = has_validation
        context["last_refresh"] = last_refresh
        context["client_validation"] = self._build_client_validation(
            switch_configs, validation_map, switch_status
        )
        context["refresh_job"] = self._latest_refresh_job()
        return context

    def post(self, request, *args, **kwargs):
        # Handle refresh button
        if "refresh_validation" in request.POST:
            return self._handle_refresh(request)

        # Handle save connections
        switch_configs = list(self._get_switch_configs())
        assets = list(self._get_rack_assets())
        connection_map = self._build_connection_map(assets, switch_configs)

        created_count = 0
        removed_count = 0
        errors = []
        dc = _rack_data_center(self.object)

        with transaction.atomic():
            for asset in assets:
                for sc in switch_configs:
                    field_name = f"port_{asset.id}_{sc.id}"
                    override_field = f"override_{asset.id}_{sc.id}"
                    new_value = request.POST.get(field_name, "").strip()
                    override_value = request.POST.get(override_field, "").strip()

                    # Resolve the target switch (override or column default).
                    if override_value:
                        target_switch = _resolve_switch(override_value, dc)
                        if target_switch is None:
                            errors.append(
                                f"{asset.hostname} / {sc.label}: "
                                f"unknown switch '{override_value}'"
                            )
                            continue
                    else:
                        target_switch = sc.switch

                    self._sync_override(sc, asset, target_switch, override_value)

                    existing = connection_map.get((asset.id, sc.id))
                    existing_label = existing["switch_port_label"] if existing else None
                    existing_switch_id = (
                        existing["actual_switch_id"] if existing else None
                    )

                    if new_value:
                        new_switch_port_label = _port_label_for_switch(new_value)
                    else:
                        new_switch_port_label = None

                    unchanged = (
                        existing_label == new_switch_port_label
                        and existing_switch_id == (
                            target_switch.id if new_switch_port_label else None
                        )
                    )
                    if unchanged:
                        continue

                    if existing and not new_switch_port_label:
                        # Disconnect
                        try:
                            asset_port = Port.objects.get(
                                label=existing["asset_port_label"],
                                data_center_asset=asset,
                            )
                            connections.disconnect(asset_port)
                            removed_count += 1
                        except Port.DoesNotExist:
                            pass
                        continue

                    if new_switch_port_label:
                        # Connect (or reconnect, possibly to a different switch)
                        try:
                            asset_port, _ = Port.objects.get_or_create(
                                label=sc.label,
                                data_center_asset=asset,
                            )
                            switch_port, _ = Port.objects.get_or_create(
                                label=new_switch_port_label,
                                data_center_asset=target_switch,
                            )
                            connections.connect(asset_port, switch_port)
                            created_count += 1
                        except Exception as e:
                            errors.append(f"{asset.hostname} / {sc.label}: {e}")

        if created_count:
            messages.success(request, f"Created/updated {created_count} connection(s).")
        if removed_count:
            messages.success(request, f"Removed {removed_count} connection(s).")
        if errors:
            for error in errors:
                messages.error(request, error)

        return HttpResponseRedirect(request.path)

    def _sync_override(self, sc, asset, target_switch, override_value):
        """Create, update or drop the per-server override for a cell."""
        if override_value and target_switch.id != sc.switch_id:
            RackSwitchConfigurationOverride.objects.update_or_create(
                rack_switch_configuration=sc,
                data_center_asset=asset,
                defaults={"switch": target_switch},
            )
        else:
            RackSwitchConfigurationOverride.objects.filter(
                rack_switch_configuration=sc,
                data_center_asset=asset,
            ).delete()

    def _handle_refresh(self, request):
        """Enqueue an asynchronous netmaker refresh for the whole rack."""
        running = SwitchportRefreshJob.objects.filter(
            rack_configuration=self.rack_configuration,
            status__in=[RefreshJobStatus.PENDING, RefreshJobStatus.IN_PROGRESS],
        ).exists()
        if running:
            messages.info(request, "A refresh is already in progress for this rack.")
            return HttpResponseRedirect(request.path)

        try:
            job = SwitchportRefreshJob.objects.create(
                rack_configuration=self.rack_configuration,
                status=RefreshJobStatus.PENDING,
            )
            InternalService("SWITCHPORTS_REFRESH").run_async(
                rack_configuration_id=self.rack_configuration.id,
                refresh_job_id=job.id,
            )
            messages.success(
                request,
                "Netmaker refresh started. Ports will be pulled into Ralph when "
                "the backend finishes.",
            )
        except Exception as e:
            logger.exception("Failed to enqueue rack refresh")
            messages.error(request, f"Failed to start refresh: {e}")

        return HttpResponseRedirect(request.path)


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
        dc = _rack_data_center(getattr(rack_config, "rack", None))
        switch = _resolve_switch(identifier, dc)
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


class RackConfigurationView(RalphDetailView):
    """Rack admin tab to edit the rack's switch columns (RackConfiguration).

    Attached to the ``Rack`` admin, so ``self.object`` is a ``Rack``. It edits
    the related ``RackConfiguration`` description and its ``RackSwitchConfiguration``
    columns (which Django admin cannot inline directly on the Rack page because
    they are nested one level below the rack).
    """

    icon = "sliders"
    label = "Rack Configuration"
    name = "rack_configuration"
    url_name = "rack-configuration"
    template_name = "switchports/rackconfiguration/rack_configuration_form.html"

    @cached_property
    def rack_configuration(self):
        rack_config, _ = RackConfiguration.objects.get_or_create(rack=self.object)
        return rack_config

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault(
            "config_form",
            RackConfigurationForm(instance=self.rack_configuration),
        )
        context.setdefault(
            "formset",
            RackSwitchConfigurationFormSet(instance=self.rack_configuration),
        )
        return context

    def post(self, request, *args, **kwargs):
        config_form = RackConfigurationForm(
            request.POST, instance=self.rack_configuration
        )
        formset = RackSwitchConfigurationFormSet(
            request.POST, instance=self.rack_configuration
        )
        if config_form.is_valid() and formset.is_valid():
            with transaction.atomic():
                config_form.save()
                formset.save()
            messages.success(request, "Rack configuration saved.")
            return HttpResponseRedirect(request.path)
        messages.error(request, "Please correct the errors below.")
        context = self.get_context_data(config_form=config_form, formset=formset)
        return self.render_to_response(context)
