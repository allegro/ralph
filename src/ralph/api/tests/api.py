# -*- coding: utf-8 -*-
from django.conf.urls import include, url

from ralph.api import RalphAPISerializer, RalphAPIViewSet
from ralph.api.routers import RalphRouter
from ralph.tests.models import Car, Foo, Manufacturer


class FooSerializer(RalphAPISerializer):
    class Meta:
        model = Foo
        # include view namespace for hyperlinked field
        extra_kwargs = {
            'url': {
                'view_name': 'test-ralph-api:foo-detail'
            }
        }


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


class CarViewSet(RalphAPIViewSet):
    queryset = Car.objects.all()
    serializer_class = CarSerializer
    filter_fields = ['manufacturer__name']


router = RalphRouter()
router.register(r'foos', FooViewSet)
router.register(r'manufacturers', ManufacturerViewSet)
router.register(r'cars', CarViewSet)
urlpatterns = [
    url(r'^test-ralph-api/', include(router.urls, namespace='test-ralph-api')),
]
