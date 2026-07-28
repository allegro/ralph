"""Asynchronous, locked, parallel netmaker refresh for a whole rack.

Triggered from the switchport grid. A single job refreshes every switch related
to the rack (column switches + per-server override switches) on a bounded thread
pool, taking a per-switch Redis lock so the lock-less backend is not hammered by
concurrent refreshes of the same switch. When the backend refresh finishes the
fresh ports are pulled back into Ralph as BackendValidationResult rows.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import django_rq
from django.conf import settings
from django.db import connections as db_connections
from django.utils import timezone

from ralph.switchports.constants import (
    DEFAULT_LOCK_BLOCKING_TIMEOUT,
    DEFAULT_LOCK_TIMEOUT,
    DEFAULT_MAX_PARALLEL,
    REFRESH_QUEUE_NAME,
)
from ralph.switchports.models import (
    RackConfiguration,
    RefreshJobStatus,
    SwitchportRefreshJob,
)
from ralph.switchports.netmaker.backend import NetmakerSwitchportBackend
from ralph.switchports.sync.refresh import rebuild_validation_for_switch
from ralph.switchports.sync.switches import iter_rack_switches

logger = logging.getLogger(__name__)


def _refresh_single_switch(switch, in_thread=True):
    """Refresh one switch: backend refresh (locked) + pull ports into Ralph.

    When ``in_thread`` is True this runs in a worker thread and manages its own
    DB connection; otherwise it runs inline in the caller's connection.
    Returns a per-switch summary dict; never raises.
    """
    entry = {"hostname": switch.hostname, "switch_id": switch.id}
    backend = NetmakerSwitchportBackend()
    per_switch_summary = {
        "refreshed_switches": 0,
        "switch_not_found": 0,
        "ports_processed": 0,
    }
    lock_timeout = getattr(
        settings, "SWITCHPORT_REFRESH_LOCK_TIMEOUT", DEFAULT_LOCK_TIMEOUT
    )
    blocking_timeout = getattr(
        settings,
        "SWITCHPORT_REFRESH_LOCK_BLOCKING_TIMEOUT",
        DEFAULT_LOCK_BLOCKING_TIMEOUT,
    )
    conn = django_rq.get_connection(REFRESH_QUEUE_NAME)
    lock = conn.lock(
        f"switchport-refresh:{switch.hostname}",
        timeout=lock_timeout,
        blocking_timeout=blocking_timeout,
    )
    acquired = False
    try:
        acquired = lock.acquire()
        if not acquired:
            entry["status"] = "locked"
            entry["error"] = "another refresh for this switch is already running"
            return entry

        # 1. Trigger the backend (netmaker) refresh. switchApp does this
        #    synchronously, so this blocks until backend data is fresh.
        backend.refresh_switch(switch.hostname)

        # 2. Pull the fresh ports into Ralph
        rebuild_validation_for_switch(backend, switch, per_switch_summary)
        if per_switch_summary["switch_not_found"]:
            entry["status"] = "switch_not_found"
        else:
            entry["status"] = "refreshed"
        entry["ports_processed"] = per_switch_summary["ports_processed"]
    except Exception as e:  # noqa
        logger.exception("Failed to refresh switch %s", switch.hostname)
        entry["status"] = "error"
        entry["error"] = f"Failed to refresh switch {str(switch)}"
    finally:
        if acquired:
            try:
                lock.release()
            except Exception:
                logger.warning(
                    "Failed to release lock for %s", switch.hostname, exc_info=True
                )
        # Threads get their own DB connection; close it to avoid leaks.
        if in_thread:
            db_connections.close_all()
    return entry


def run_rack_refresh(rack_configuration_id, refresh_job_id):
    """RQ entrypoint: refresh every switch related to a rack in parallel."""
    try:
        job = SwitchportRefreshJob.objects.get(pk=refresh_job_id)
    except SwitchportRefreshJob.DoesNotExist:
        logger.error("SwitchportRefreshJob %s not found", refresh_job_id)
        return

    job.status = RefreshJobStatus.IN_PROGRESS
    job.started_at = timezone.now()
    job.save(update_fields=["status", "started_at", "modified"])

    try:
        rack_configuration = RackConfiguration.objects.get(pk=rack_configuration_id)
        switches = iter_rack_switches(rack_configuration)
    except Exception as e:  # noqa
        logger.exception("Failed to enumerate switches for rack refresh")
        job.status = RefreshJobStatus.ERROR
        job.error = str(e)
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "error", "finished_at", "modified"])
        return

    max_parallel = getattr(
        settings, "SWITCHPORT_REFRESH_MAX_PARALLEL", DEFAULT_MAX_PARALLEL
    )
    entries = []
    if switches:
        if max_parallel <= 1:
            # Run inline (no thread pool): simpler and avoids cross-thread
            # visibility issues; used when the backend must not be hit in
            # parallel at all.
            for switch in switches:
                entries.append(_refresh_single_switch(switch, in_thread=False))
        else:
            with ThreadPoolExecutor(max_workers=max_parallel) as executor:
                futures = [
                    executor.submit(_refresh_single_switch, switch)
                    for switch in switches
                ]
                for future in as_completed(futures):
                    entries.append(future.result())

    summary = {
        "switches": entries,
        "refreshed_switches": sum(1 for e in entries if e["status"] == "refreshed"),
        "switch_not_found": sum(
            1 for e in entries if e["status"] == "switch_not_found"
        ),
        "ports_processed": sum(e.get("ports_processed", 0) for e in entries),
        "errors": [e for e in entries if e["status"] in ("error", "locked")],
    }

    job.summary = summary
    job.status = (
        RefreshJobStatus.ERROR if summary["errors"] else RefreshJobStatus.SUCCESS
    )
    job.finished_at = timezone.now()
    job.save(update_fields=["summary", "status", "finished_at", "modified"])
