"""Round-2 tests written from the surviving-mutant analysis (report 5.4).

Each test names the mutmut ids it was written to kill. Categories:
  WA = weak assertion (message checked by substring only)
  MT = missing test (behaviour never exercised)
  SD = schema drift (model change without a migration; invisible to tests
       because the test DB schema is reused)
"""

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command

pytestmark = pytest.mark.django_db


# ---------- SD: one guard kills every field-option / Meta mutant ----------
# (null/blank/max_length/default/verbose_name/help_text/unique/unique_together,
#  limit_models, removed fields). Business reason: a model change shipped
# without a migration breaks deployment and silently drops DB constraints
# such as "one licence per asset" (BR4).
def test_models_and_migrations_are_in_sync():
    try:
        call_command("makemigrations", "licences", "--check", "--dry-run", verbosity=0)
    except SystemExit as exc:  # exit code 1 == pending model changes
        pytest.fail(f"licences models differ from migrations (exit {exc.code})")


# ---------- WA: exact, user-facing error messages (ids 161, 166, 182, 186) ----------


def test_region_error_message_is_exact(make_licence, make_bo_asset, region_pk, region_uk):
    from ralph.licences.models import BaseObjectLicence

    bol = BaseObjectLicence(
        licence=make_licence(region=region_pk),
        base_object=make_bo_asset(region=region_uk),
        quantity=1,
    )
    with pytest.raises(ValidationError) as exc:
        bol.clean()
    assert exc.value.messages == ["Asset region is in a different region than licence."]


# ---------- MT: audit trail of assignments (id 142) ----------


def test_licence_assignments_are_audited_by_reversion():
    from reversion import revisions as reversion
    from ralph.licences.models import BaseObjectLicence

    assert reversion.is_registered(BaseObjectLicence)


# ---------- MT: display string used in the assignment autocomplete (id 116) ----------


def test_autocomplete_string_exact(make_licence):
    from ralph.licences.models import Licence

    lic = Licence.objects.get(pk=make_licence(number_bought=3).pk)
    assert lic.autocomplete_str == "3 (3 free) x {} - {} ({})".format(
        lic.software.name, lic.invoice_date, lic.niw
    )


# ---------- MT: polymorphic manager used by the API (id 110) ----------


def test_polymorphic_manager_returns_licences(make_licence):
    from ralph.licences.models import Licence

    lic = make_licence()
    assert list(Licence.polymorphic_objects.filter(pk=lic.pk)) == [lic]


# ---------- MT: field-level permission mapping for used/free (ids 131,132,137,138) ----------
# Ralph hides computed columns from users who may not see number_bought
# (PermByFieldMixin). Losing the mapping exposes seat counts (security, role B).
@pytest.mark.parametrize("prop", ["used", "free"])
def test_seat_counters_are_guarded_by_number_bought_permission(prop):
    from ralph.licences.models import Licence

    assert Licence.__dict__[prop]._permission_field == "number_bought"


# ---------- MT: dashboard registration (ids 3, 4, 30, 31) ----------
@pytest.mark.parametrize("model_name", ["Software", "Licence"])
def test_models_are_available_in_dashboards(model_name):
    from ralph.licences import models

    assert getattr(models, model_name)._allow_in_dashboard is True
