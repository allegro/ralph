"""BR2 - Region decision (rule with more than one Boolean condition).

Source: src/ralph/licences/models.py, BaseObjectLicence.clean

    if bo_asset and self.licence and self.licence.region_id != bo_asset.region_id:
        raise ValidationError("Asset region is in a different region than licence.")

Conditions
    A = bo_asset is truthy          (the assigned object is a Back Office asset)
    B = self.licence is truthy      (a licence is set)
    C = licence.region != asset.region
Decision D = A and B and C  -> reject

MCC (Python evaluates left to right with short-circuit, so 4 feasible rows):
    row | A | B | C | D      | test
    ----+---+---+---+--------+------------------------------------------
     1  | F | - | - | accept | test_mcc_row1_non_backoffice_object_skips_rule
     2  | T | F | - | n/a    | INFEASIBLE: self.licence raises
        |   |   |   |        | RelatedObjectDoesNotExist (test_mcc_row2_...)
     3  | T | T | F | accept | test_mcc_row3_same_region_is_accepted
     4  | T | T | T | reject | test_mcc_row4_different_region_is_rejected

MC/DC pairs (each pair differs only in one condition and flips D):
    A: rows 1 vs 4
    C: rows 3 vs 4
    B: no independence pair is possible (row 2 cannot be reached) -> justified
       in the report as an infeasible / defensive condition.
"""

import pytest
from django.core.exceptions import ValidationError

pytestmark = [pytest.mark.django_db, pytest.mark.br2]


def test_mcc_row1_non_backoffice_object_skips_rule(make_licence, region_uk):
    """A = False: a Data Center asset is not regionalised, rule does not apply."""
    from ralph.data_center.tests.factories import DataCenterAssetFactory
    from ralph.licences.models import BaseObjectLicence

    lic = make_licence()  # PK region
    dc_asset = DataCenterAssetFactory()
    BaseObjectLicence(licence=lic, base_object=dc_asset, quantity=1).clean()


def test_mcc_row2_missing_licence_raises_before_condition_b(make_bo_asset):
    """A = True, B = False is unreachable: Django raises on the FK access."""
    from ralph.licences.models import BaseObjectLicence

    bol = BaseObjectLicence(base_object=make_bo_asset(), quantity=1)
    with pytest.raises(BaseObjectLicence.licence.RelatedObjectDoesNotExist):
        bol.clean()


def test_mcc_row3_same_region_is_accepted(make_licence, make_bo_asset, region_pk):
    from ralph.licences.models import BaseObjectLicence

    lic = make_licence(region=region_pk)
    asset = make_bo_asset(region=region_pk)
    BaseObjectLicence(licence=lic, base_object=asset, quantity=1).clean()


def test_mcc_row4_different_region_is_rejected(make_licence, make_bo_asset, region_pk, region_uk):
    from ralph.licences.models import BaseObjectLicence

    lic = make_licence(region=region_pk)
    asset = make_bo_asset(region=region_uk)
    with pytest.raises(ValidationError, match="different region"):
        BaseObjectLicence(licence=lic, base_object=asset, quantity=1).clean()


def test_api_serializer_runs_the_same_model_rule(
    make_licence, make_bo_asset, region_pk, region_uk
):
    """BaseObjectLicenceSerializer.validate delegates to clean()."""
    from ralph.licences.api import BaseObjectLicenceSerializer

    lic = make_licence(region=region_pk)
    ok_asset = make_bo_asset(region=region_pk)
    bad_asset = make_bo_asset(region=region_uk)
    s = BaseObjectLicenceSerializer()
    data = {"licence": lic, "base_object": ok_asset, "quantity": 1}
    assert s.validate(data) == data
    with pytest.raises(ValidationError):
        s.validate({"licence": lic, "base_object": bad_asset, "quantity": 1})
