"""Deterministic synthetic data for the SQE licence workflows.

Run (repo root, Ralph env/DB configured):
    uv run ralph shell < tests/team/seed/seed_sqe.py

Creates (idempotent - safe to run twice):
  Regions : PK-Islamabad, UK-London
  Roles   : group "SQE Asset Manager" (full licence + back-office rights, all regions)
            group "SQE Regional Clerk" (view licences, assign licence to assets,
            no licence create/change/delete, PK region only)
  Users   : sqe_manager / Sqe-Manager-1   (Asset Manager)
            sqe_clerk   / Sqe-Clerk-1     (Regional Clerk)
  Licences: "Office 365 E3"  5 seats PK   (niw SQE-LIC-001)
            "AutoCAD 2026"   1 seat  UK   (niw SQE-LIC-002)
            "Zoom Pro"       2 seats PK, both used (niw SQE-LIC-003)
  Assets  : SQE-BO-001..004 (PK, status new/new/in use/free), SQE-BO-101 (UK, new)
  Transitions on BackOfficeAsset.status: release / return / liquidate
"""

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from ralph.accounts.models import RalphUser, Region
from ralph.assets.models import AssetHolder, AssetModel, Category, ObjectModelType
from ralph.back_office.models import BackOfficeAsset, BackOfficeAssetStatus as S, Warehouse
from ralph.lib.transitions.models import Action, Transition, TransitionModel
from ralph.licences.models import BaseObjectLicence, Licence, LicenceType, Software

pk, _ = Region.objects.get_or_create(name="PK-Islamabad")
uk, _ = Region.objects.get_or_create(name="UK-London")


def perms(*codenames):
    return list(Permission.objects.filter(codename__in=codenames))


manager_group, _ = Group.objects.get_or_create(name="SQE Asset Manager")
manager_group.permissions.set(
    Permission.objects.filter(content_type__app_label__in=["licences", "back_office"])
)
clerk_group, _ = Group.objects.get_or_create(name="SQE Regional Clerk")
# Ralph checks permissions per field too (e.g. view_licence_niw_field), so the
# clerk gets every view permission of licences/back office + adding assignments.
clerk_group.permissions.set(
    list(
        Permission.objects.filter(
            content_type__app_label__in=["licences", "back_office", "assets"],
            codename__startswith="view_",
        )
    )
    + perms("add_baseobjectlicence")
)


def user(username, password, group, regions, superuser=False):
    u, created = RalphUser.objects.get_or_create(username=username, defaults={"is_staff": True})
    u.is_staff, u.is_superuser = True, superuser
    u.set_password(password)
    u.save()
    u.groups.set([group])
    u.regions.set(regions)
    return u


manager = user("sqe_manager", "Sqe-Manager-1", manager_group, [pk, uk])
clerk = user("sqe_clerk", "Sqe-Clerk-1", clerk_group, [pk])

lt, _ = LicenceType.objects.get_or_create(name="per user")


def licence(niw, sw_name, seats, region):
    sw, _ = Software.objects.get_or_create(name=sw_name)
    lic, _ = Licence.objects.get_or_create(
        niw=niw, defaults=dict(software=sw, licence_type=lt, number_bought=seats, region=region)
    )
    return lic


office = licence("SQE-LIC-001", "Office 365 E3", 5, pk)
autocad = licence("SQE-LIC-002", "AutoCAD 2026", 1, uk)
zoom = licence("SQE-LIC-003", "Zoom Pro", 2, pk)

cat, _ = Category.objects.get_or_create(name="Laptop")
model, _ = AssetModel.objects.get_or_create(
    name="ThinkPad T14", defaults={"type": ObjectModelType.back_office, "category": cat}
)
wh, _ = Warehouse.objects.get_or_create(name="Islamabad HQ")
# Ralph requires "property of" on assets created through the API/UI.
holder, _ = AssetHolder.objects.get_or_create(name="SQE Holding")


def asset(barcode, region, status, user=None):
    a, _ = BackOfficeAsset.objects.get_or_create(
        barcode=barcode,
        defaults=dict(
            region=region,
            status=status,
            model=model,
            warehouse=wh,
            hostname=barcode.lower(),
            user=user,
            property_of=holder,
        ),
    )
    if a.property_of_id is None:
        a.property_of = holder
        a.save()
    return a


bo1 = asset("SQE-BO-001", pk, S.new)
bo2 = asset("SQE-BO-002", pk, S.new)
bo3 = asset("SQE-BO-003", pk, S.used, user=manager)
bo4 = asset("SQE-BO-004", pk, S.free)
bo_uk = asset("SQE-BO-101", uk, S.new)

# Zoom Pro fully used (2/2) -> boundary data for BR1
BaseObjectLicence.objects.get_or_create(licence=zoom, base_object=bo3, defaults={"quantity": 2})

tm = TransitionModel.get_for_field(BackOfficeAsset(), "status")


def transition(name, sources, target, actions):
    t, _ = Transition.objects.get_or_create(
        name=name, model=tm, defaults={"source": [s.id for s in sources], "target": target.id}
    )
    for a in actions:
        act, _ = Action.objects.get_or_create(name=a)
        act.content_type.add(ContentType.objects.get_for_model(BackOfficeAsset))
        t.actions.add(act)


transition("release", [S.new, S.free], S.used, ["assign_user", "assign_licence"])
transition("return", [S.used], S.free, ["unassign_user", "unassign_licences"])
transition("liquidate", [S.free, S.damaged], S.liquidated, [])

# Roles are (re)applied last: per-transition permissions (can_run_release_transition,
# ...) only exist once the transitions above have been created.
manager_group.permissions.set(
    list(Permission.objects.filter(content_type__app_label__in=["licences", "back_office"]))
    + list(Permission.objects.filter(codename__startswith="can_view_extra_"))
    + list(
        Permission.objects.filter(
            content_type__app_label="assets",
            codename__in=["view_assetholder", "view_assetmodel", "view_category"],
        )
    )
    + perms("view_ralphuser")
    + list(
        Permission.objects.filter(
            content_type__app_label="transitions", codename__startswith="view_"
        )
    )
)
clerk_group.permissions.set(
    list(
        Permission.objects.filter(
            content_type__app_label__in=["licences", "back_office", "assets"],
            codename__startswith="view_",
        )
    )
    + perms("add_baseobjectlicence")
)

print(
    "SQE seed OK:",
    Licence.objects.filter(niw__startswith="SQE-").count(),
    "licences,",
    BackOfficeAsset.objects.filter(barcode__startswith="SQE-").count(),
    "assets",
)
