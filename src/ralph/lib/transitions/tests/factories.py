from django.contrib.contenttypes.models import ContentType
from factory import DjangoModelFactory, SubFactory, Sequence, Iterator
from factory.fuzzy import FuzzyText

from ralph.back_office.models import BackOfficeAsset
from ralph.data_center.models import DataCenterAsset, Accessory
from ralph.lib.transitions.models import Transition, TransitionModel


class TransitionModelFactory(DjangoModelFactory):
    content_type =  Iterator([ContentType.objects.get_for_model(m) for m in [BackOfficeAsset, DataCenterAsset]])
    field_name = FuzzyText(length=10)

    class Meta:
        model = TransitionModel
        django_get_or_create = ['content_type', 'field_name']


class TransitionFactory(DjangoModelFactory):
    name = FuzzyText(length=10)
    model = SubFactory(TransitionModelFactory)

    class Meta:
        model = Transition
        django_get_or_create = ['name', ]
