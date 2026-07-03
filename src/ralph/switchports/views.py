import logging

from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect

from ralph.admin.views.extra import RalphDetailView
from ralph.data_center.models import DataCenterAsset
from ralph.switchports import connections
from ralph.switchports.models import (
    BackendValidationResult,
    Port,
    ValidationStatus,
)
from ralph.switchports.validation import refresh_validation_for_rack

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


class RackSwitchportGridView(RalphDetailView):
    icon = "th"
    label = "Switchport Grid"
    name = "switchport_grid"
    url_name = "switchport-grid"
    template_name = "switchports/rackconfiguration/switchport_grid.html"

    def _get_rack_assets(self):
        """Get all DataCenterAssets in this rack, ordered by position."""
        rack = self.object.rack
        return (
            DataCenterAsset.objects.filter(rack=rack)
            .select_related("model", "model__category")
            .order_by("-position", "slot_no", "hostname")
        )

    def _get_switch_configs(self):
        """Get all RackSwitchConfigurations for this rack, ordered by label."""
        return self.object.switches.select_related("switch").order_by("label")

    def _build_connection_map(self, assets, switch_configs):
        """Build a map of (asset_id, switch_config_id) -> port info.

        For each asset, look at its ports and their connections.
        If a port is connected to a port on one of the configured switches,
        record the mapping.
        """
        switch_id_to_config = {sc.switch_id: sc for sc in switch_configs}
        switch_ids = set(switch_id_to_config.keys())
        asset_ids = [a.id for a in assets]

        if not asset_ids or not switch_ids:
            return {}

        asset_ports = (
            Port.objects.filter(data_center_asset_id__in=asset_ids)
            .select_related(
                "connectionmember__connection",
            )
            .prefetch_related(
                "connectionmember__connection__members__port",
            )
        )

        connection_map = {}
        for port in asset_ports:
            conn_member = getattr(port, "connectionmember", None)
            if not conn_member:
                continue
            connection = conn_member.connection
            for member in connection.members.all():
                if member.port_id == port.id:
                    continue
                remote_port = member.port
                if remote_port.data_center_asset_id in switch_ids:
                    sc = switch_id_to_config[remote_port.data_center_asset_id]
                    connection_map[(port.data_center_asset_id, sc.id)] = {
                        "switch_port_label": remote_port.label,
                        "asset_port_label": port.label,
                    }
        return connection_map

    def _build_validation_map(self, switch_configs):
        """Build a map of (switch_id, port_label) -> BackendValidationResult.

        Also returns per-switch status (SWITCH_NOT_FOUND if the sentinel exists).
        """
        results = BackendValidationResult.objects.filter(
            rack_configuration=self.object,
        ).select_related("remote_asset")

        validation_map = {}
        switch_status = {}
        for result in results:
            if result.port_label == "__switch__":
                switch_status[result.switch_id] = result.status
            else:
                validation_map[(result.switch_id, result.port_label)] = result

        return validation_map, switch_status

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assets = list(self._get_rack_assets())
        switch_configs = list(self._get_switch_configs())
        connection_map = self._build_connection_map(assets, switch_configs)
        validation_map, switch_status = self._build_validation_map(switch_configs)

        # Check if we have any validation results at all
        has_validation = bool(validation_map) or bool(switch_status)

        # Get last refresh time
        last_refresh = None
        if has_validation:
            last_result = (
                BackendValidationResult.objects.filter(rack_configuration=self.object)
                .order_by("-modified")
                .first()
            )
            if last_result:
                last_refresh = last_result.modified

        rows = []
        for asset in assets:
            cells = []
            for sc in switch_configs:
                conn_info = connection_map.get((asset.id, sc.id))
                if conn_info:
                    switch_port_label = conn_info["switch_port_label"]
                    display_value = switch_port_label
                    if switch_port_label.startswith("0/0/"):
                        display_value = switch_port_label[4:]
                else:
                    switch_port_label = None
                    display_value = ""

                # Validation for this cell
                validation = None
                if switch_port_label and sc.switch_id in switch_status:
                    # Switch not found in backend
                    validation = {
                        "status": ValidationStatus.SWITCH_NOT_FOUND,
                        "css_class": "validation-error",
                        "label": "SWITCH N/F",
                    }
                elif switch_port_label:
                    vr = validation_map.get((sc.switch_id, switch_port_label))
                    if vr is None and has_validation:
                        validation = {
                            "status": ValidationStatus.PORT_NOT_FOUND,
                            "css_class": "validation-warning",
                            "label": "PORT N/F",
                        }
                    elif vr is not None:
                        if vr.status == ValidationStatus.ASSET_FOUND:
                            match = (
                                vr.remote_asset_id == asset.id
                                if vr.remote_asset_id
                                else False
                            )
                            validation = {
                                "status": ValidationStatus.ASSET_FOUND,
                                "css_class": "validation-ok"
                                if match
                                else "validation-mismatch",
                                "label": vr.remote_asset.hostname
                                if vr.remote_asset
                                else vr.remote_hostname,
                                "remote_asset": vr.remote_asset,
                                "match": match,
                            }
                        elif vr.status == ValidationStatus.ASSET_CONFLICT:
                            validation = {
                                "status": ValidationStatus.ASSET_CONFLICT,
                                "css_class": "validation-error",
                                "label": f"CONFLICT ({vr.remote_hostname})"
                                if vr.remote_hostname
                                else "CONFLICT",
                                "remote_asset": vr.remote_asset,
                            }
                        elif vr.status == ValidationStatus.PORT_NOT_FOUND:
                            validation = {
                                "status": ValidationStatus.PORT_NOT_FOUND,
                                "css_class": "validation-warning",
                                "label": "empty",
                            }

                cells.append(
                    {
                        "switch_config": sc,
                        "value": display_value,
                        "field_name": f"port_{asset.id}_{sc.id}",
                        "validation": validation,
                    }
                )
            rows.append({"asset": asset, "cells": cells})

        context["switch_configs"] = switch_configs
        context["switch_status"] = switch_status
        context["rows"] = rows
        context["has_validation"] = has_validation
        context["last_refresh"] = last_refresh
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

        with transaction.atomic():
            for asset in assets:
                for sc in switch_configs:
                    field_name = f"port_{asset.id}_{sc.id}"
                    new_value = request.POST.get(field_name, "").strip()
                    existing = connection_map.get((asset.id, sc.id))
                    existing_label = existing["switch_port_label"] if existing else None

                    if new_value:
                        new_switch_port_label = _port_label_for_switch(new_value)
                    else:
                        new_switch_port_label = None

                    if existing_label == new_switch_port_label:
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
                        # Connect (or reconnect)
                        try:
                            asset_port, _ = Port.objects.get_or_create(
                                label=sc.label,
                                data_center_asset=asset,
                            )
                            switch_port, _ = Port.objects.get_or_create(
                                label=new_switch_port_label,
                                data_center_asset=sc.switch,
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

    def _handle_refresh(self, request):
        """Handle the 'Refresh from netmaker' button."""
        try:
            summary = refresh_validation_for_rack(self.object)
            if summary["switch_not_found"]:
                messages.warning(
                    request,
                    f"{summary['switch_not_found']} switch(es) not found in backend.",
                )
            messages.success(
                request,
                f"Refreshed {summary['refreshed_switches']} switch(es), "
                f"{summary['ports_processed']} port(s) processed.",
            )
        except Exception as e:
            logger.exception("Failed to refresh validation from backend")
            messages.error(request, f"Failed to refresh from backend: {e}")

        return HttpResponseRedirect(request.path)
