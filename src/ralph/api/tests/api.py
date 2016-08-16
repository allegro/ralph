# -*- coding: utf-8 -*-
from django.conf.urls import include, url

from ralph.api import RalphAPISerializer, RalphAPIViewSet
from ralph.api.fields import StrField
from ralph.api.routers import RalphRouter
from ralph.tests.models import Bar, Car, Foo, Manufacturer


class FooSerializer(RalphAPISerializer):
    __str__ = StrField()
    str_with_type = StrField(show_type=True, label='__str2__')

    class Meta:
        model = Foo
        # include view namespace for hyperlinked field
        extra_kwargs = {
            'url': {
                'view_name': 'test-ralph-api:foo-detail'
            }
        }


class BarSerializer(RalphAPISerializer):
    class Meta:
        model = Bar


class ManufacturerSerializer(RalphAPISerializer):
    class Meta:
        model = Manufacturer
        # include view namespace for hyperlinked field
        extra_kwargs = {
            'url': {
                'view_name': 'test-ralph-api:manufacturer-detail'
            }
        }


class ManufacturerSerializer2(ManufacturerSerializer):
    def validate_name(self, value):
        return value


class CarSerializer(RalphAPISerializer):
    class Meta:
        model = Car
        # include view namespace for hyperlinked field
        extra_kwargs = {
            'url': {
                'view_name': 'test-ralph-api:car-detail'
            }
        }
        depth = 1


class CarSerializer2(CarSerializer):
    manufacturer = ManufacturerSerializer2()


class FooViewSet(RalphAPIViewSet):
    queryset = Foo.objects.all()
    serializer_class = FooSerializer


class ManufacturerViewSet(RalphAPIViewSet):
    queryset = Manufacturer.objects.all()
    serializer_class = ManufacturerSerializer
    save_serializer_class = ManufacturerSerializer2
    extended_filter_fields = {
        'some_field': ['name', 'country'],
    }


class CarViewSet(RalphAPIViewSet):
    queryset = Car.objects.all()
    serializer_class = CarSerializer
    filter_fields = ['manufacturer__name']


class BarViewSet(RalphAPIViewSet):
    queryset = Bar.objects.all()
    serializer_class = BarSerializer
    filter_fields = ['id']


router = RalphRouter()
router.register(r'foos', FooViewSet)
router.register(r'manufacturers', ManufacturerViewSet)
router.register(r'cars', CarViewSet)
router.register(r'bars', BarViewSet)
urlpatterns = [
    url(r'^test-ralph-api/', include(router.urls, namespace='test-ralph-api')),
]
