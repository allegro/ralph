from django.contrib.contenttypes.models import ContentType
from factory import DjangoModelFactory, Sequence, SubFactory
from factory.fuzzy import FuzzyText

from ralph.accounts.tests.factories import UserFactory
from ralph.back_office.models import BackOfficeAsset
from ralph.back_office.tests.factories import BackOfficeAssetFactory
from ralph.data_center.models import DataCenterAsset
from ralph.data_center.tests.factories import DataCenterAssetFullFactory
from ralph.lib.transitions.models import (
    Transition,
    TransitionJob,
    TransitionModel,
    TransitionsHistory
)


class TransitionModelFactory(DjangoModelFactory):
    content_type =  Sequence(lambda n: ContentType.objects.get_for_model([BackOfficeAsset, DataCenterAsset][n % 2]))
    field_name = 'status'

    class Meta:
        model = TransitionModel
        django_get_or_create = ['content_type', 'field_name']


class TransitionFactory(DjangoModelFactory):
    name = FuzzyText(length=10)
    model = SubFactory(TransitionModelFactory)
    source = ["new", "used"]
    target = "used"

    class Meta:
        model = Transition
        django_get_or_create = ['name', ]


class TransitionJobFactory(DjangoModelFactory):
    content_type = Sequence(lambda n: ContentType.objects.get_for_model([BackOfficeAsset, DataCenterAsset][n % 2]))
    object_id = Sequence(lambda n: [BackOfficeAssetFactory, DataCenterAssetFullFactory][n % 2]().id)
    transition = SubFactory(TransitionFactory)

    class Meta:
        model = TransitionJob


class TransitionsHistoryFactory(DjangoModelFactory):
    content_type =  Sequence(lambda n: ContentType.objects.get_for_model([BackOfficeAsset, DataCenterAsset][n % 2]))
    transition_name = FuzzyText(length=10)
    source = "new"
    target = "used"
    object_id = Sequence(lambda n: [BackOfficeAssetFactory, DataCenterAssetFullFactory][n % 2]().id)
    logged_user = SubFactory(UserFactory)

    class Meta:
        model = TransitionsHistory
