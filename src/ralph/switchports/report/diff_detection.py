import logging

from django.db.models import Q

from ralph.switchports.connections.core import connected_to
from ralph.switchports.models import BackendValidationResult, Port, RackConfiguration
from ralph.switchports.models.validation import SwitchportDiffStatus, DiffEntry


def compare(vr: BackendValidationResult) -> DiffEntry:
    """Check BackendValidationResult and return a new DiffEntry"""
    switch = vr.switch
    label = vr.port_label
    port = Port.objects.filter(data_center_asset=switch, label=label).first()
    asset = vr.remote_asset
    if not is_validated(vr):
        return DiffEntry(
            switch=switch,
            label=label,
            status=SwitchportDiffStatus.NOT_VALIDATED.value,
            netmaker_asset=None,
            ralph_asset=None,
        )
    if not port:
        return DiffEntry(
            switch=switch,
            label=label,
            status=SwitchportDiffStatus.PORT_MISSING.value,
            ralph_asset=None,
            netmaker_asset=None,
        )
    if not asset:
        return DiffEntry(
            switch=switch,
            label=label,
            status=SwitchportDiffStatus.NETMAKER_EMPTY.value,
            ralph_asset=None,
            netmaker_asset=None,
        )
    server_port = connected_to(port)
    if not server_port or not (ralph_server := server_port.data_center_asset):
        return DiffEntry(
            switch=switch,
            label=label,
            status=SwitchportDiffStatus.RALPH_EMPTY.value,
            ralph_asset=None,
            netmaker_asset=asset,
        )
    if ralph_server.id == asset.id:
        return DiffEntry(
            switch=switch,
            label=label,
            status=SwitchportDiffStatus.SAME_ASSET.value,
            ralph_asset=ralph_server,
            netmaker_asset=asset,
        )
    else:
        return DiffEntry(
            switch=switch,
            label=label,
            status=SwitchportDiffStatus.ASSET_MISMATCH.value,
            ralph_asset=ralph_server,
            netmaker_asset=asset,
        )


def compare_all():
    """
    take all validation results and discard those with backend_validation=False as NOT_SYNCED
    the rest - VR
    take all validation results with remote_asset (VRRA)
    take all switch ports (SP)
    take all switch ports connected to other assets (SPRA)
    then:
    ??? do we find NOT_SYNCED and NO_PORT_ON_NETMAKER ???
    ??? how we handle backend_validation flag + override ???
    (SP ∖ SPRA) ∩ (VR ∖ VRRA) - BOTH_EMPTY
    SPRA ∩ (VR ∖ VRRA) - NETMAKER_EMPTY
    (SP ∖ SPRA) ∩ VRRA - RALPH_EMPTY
    for each asset(spra) and asset(vrra) in SPRA ∩ VRRA:
        spra != vrra - ASSET_MISMATCH
        spra == vrra – SAME_ASSET
    """
    entries: list[DiffEntry] = [
        compare(vr)
        for vr in BackendValidationResult.objects.select_related("switch", "remote_asset").all()
    ]
    if not entries:
        logging.error("No validation results – exiting to prevent data corruption")
        return
    delete_all_unmatched(entries)

    for entry in entries:
        existing_entry: DiffEntry | None = DiffEntry.objects.filter(
            switch=entry.switch, label=entry.label
        ).first()
        overwrite_if_necessary(entry, existing_entry)


def delete_all_unmatched(entries: list[DiffEntry]):
    existing_entries_query = Q()
    for obj in entries:
        existing_entries_query |= Q(switch=obj.switch, label=obj.label)
    deleted = DiffEntry.objects.exclude(existing_entries_query).delete()
    logging.warning("Deleted %s not matched entries", deleted)


def overwrite_if_necessary(entry: DiffEntry, existing_entry: DiffEntry | None) -> None:
    if _should_create_new(entry, existing_entry):
        if existing_entry is not None:
            existing_entry.delete()
        entry.save()


def _should_create_new(entry: DiffEntry, existing_entry: DiffEntry | None) -> bool:
    if existing_entry is None:
        return True

    if entry.status != existing_entry.status:
        return True

    return entry.status in {
        SwitchportDiffStatus.ASSET_MISMATCH.value,
        SwitchportDiffStatus.SAME_ASSET.value,
    } and (
        entry.netmaker_asset != existing_entry.netmaker_asset
        or entry.ralph_asset != existing_entry.ralph_asset
    )


def is_validated(vr: BackendValidationResult) -> bool:
    """Record is validated if related switch is validated for at least 1 rack

    This can lead to some false positives"""
    return RackConfiguration.objects.filter(
        switches__switch=vr.switch,
        switches__backend_validation=True,
    ).exists()
