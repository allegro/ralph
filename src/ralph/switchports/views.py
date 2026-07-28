import logging

from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect, JsonResponse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from ralph.admin.views.extra import RalphDetailView
from ralph.lib.external_services import InternalService
from ralph.switchports import grid
from ralph.switchports.constants import (
    grid_force_field,
    grid_override_field,
    grid_port_field,
)
from ralph.switchports.forms import (
    RackConfigurationForm,
    RackSwitchConfigurationFormSet,
)
from ralph.switchports.grid_edit import CellEdit, apply_cell_edit
from ralph.switchports.models import (
    BackendValidationResult,
    RackConfiguration,
    RefreshJobStatus,
    SwitchportRefreshJob,
)
from ralph.switchports.rackconfig.overrides import build_override_map
from ralph.switchports.rackconfig.switch_resolver import rack_data_center
from ralph.switchports.sync import iter_rack_switches

logger = logging.getLogger(__name__)


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

    def _latest_refresh_job(self):
        return (
            SwitchportRefreshJob.objects.filter(
                rack_configuration=self.rack_configuration
            )
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
        assets = list(grid.get_rack_assets(self.object))
        switch_configs = list(grid.get_switch_configs(self.rack_configuration))
        override_map = build_override_map(switch_configs)
        connection_map = grid.build_connection_map(assets, switch_configs)
        validation_map, switch_status = grid.build_validation_map(
            self.rack_configuration
        )

        # Check if we have any validation results at all
        has_validation = bool(validation_map) or bool(switch_status)

        # Get last refresh time
        last_refresh = None
        if has_validation:
            switches = iter_rack_switches(self.rack_configuration)
            last_refresh_dict = {}
            for switch in switches:
                last_result = (
                    BackendValidationResult.objects.filter(switch=switch)
                    .order_by("-modified")
                    .first()
                )
                if last_result:
                    last_refresh_dict[switch.barcode] = last_result.modified.strftime(
                        "%d/%m/%y %H:%M"
                    )
                else:
                    last_refresh_dict[switch.barcode] = _("Never")
            if last_refresh_dict:
                last_refresh = ", ".join(
                    {f"{k} => {v}" for k, v in last_refresh_dict.items()}
                )

        context["switch_configs"] = switch_configs
        context["switch_status"] = switch_status
        conflicts = getattr(self, "_conflicts", {})
        context["rows"] = grid.build_grid_rows(
            assets,
            switch_configs,
            override_map,
            connection_map,
            validation_map,
            switch_status,
            has_validation,
            conflicts=conflicts,
        )
        context["has_conflicts"] = bool(conflicts)
        context["has_validation"] = has_validation
        context["last_refresh"] = last_refresh
        context["client_validation"] = grid.build_client_validation(
            switch_configs, validation_map, switch_status
        )
        context["refresh_job"] = self._latest_refresh_job()
        return context

    def post(self, request, *args, **kwargs):
        # Handle refresh button
        if "refresh_validation" in request.POST:
            return self._handle_refresh(request)

        return self._save_connections(request)

    def _save_connections(self, request):
        """Apply the grid edits, deferring any conflicting port steals.

        Non-conflicting cells are applied immediately. If any cell would steal a
        switch port already used by another asset (and was not explicitly
        confirmed), the whole grid is re-rendered with those cells highlighted
        and an "overwrite" checkbox, so the user decides per conflict.
        """
        switch_configs = list(grid.get_switch_configs(self.rack_configuration))
        assets = list(grid.get_rack_assets(self.object))
        connection_map = grid.build_connection_map(assets, switch_configs)
        dc = rack_data_center(self.object)

        created_count = 0
        removed_count = 0
        errors = []
        conflicts = {}

        with transaction.atomic():
            for asset in assets:
                for sc in switch_configs:
                    edit = CellEdit(
                        new_value=request.POST.get(
                            grid_port_field(asset.id, sc.id), ""
                        ),
                        override_value=request.POST.get(
                            grid_override_field(asset.id, sc.id), ""
                        ),
                        forced=grid_force_field(asset.id, sc.id) in request.POST,
                    )
                    result = apply_cell_edit(asset, sc, edit, connection_map, dc)
                    created_count += result.created
                    removed_count += result.removed
                    if result.error:
                        errors.append(result.error)
                    if result.conflict is not None:
                        conflicts[(asset.id, sc.id)] = result.conflict

        if created_count:
            messages.success(request, f"Created/updated {created_count} connection(s).")
        if removed_count:
            messages.success(request, f"Removed {removed_count} connection(s).")
        for error in errors:
            messages.error(request, error)

        if conflicts:
            messages.warning(
                request,
                f"{len(conflicts)} switch port(s) are already in use. Tick "
                "'overwrite' on the highlighted cells and save again to "
                "reassign them.",
            )
            self._conflicts = conflicts
            return self.render_to_response(self.get_context_data())

        return HttpResponseRedirect(request.path)

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
