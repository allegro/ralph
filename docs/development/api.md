# Ralph API resources

## How to create new API resource based on Django model

```django
# model
from django.db import models

class Foo(model.Model):
    bar = models.CharField(max_length=10)


# API
from ralph.api import RalphAPISerializer, RalphAPIViewSet, router


class FooSerializer(RalphAPISerializer):
    class Meta:
        model = Foo


class FooViewSet(RalphAPIViewSet):
    queryset = Foo.objects.all()
    serializer_class = FooSerializer


# use Ralph router instance to register new viewset
router.register(r'foos', FooViewSet)
```

## What are built-in features of Ralph API classes?

### `RalphAPISerializer`
* include both object PK and its url (see `ralph.api.serializers.RalphAPISerializer.get_default_field_names` for details).
* every sub-serializer (even instantiated directly as a field in other serializer) have current context set.
* use `ralph.api.serializers.ReversedChoiceField` for all choice fields - this serializer allow to pass value by name instead of key. Additionally it present value in user-friendly format by-name. This field works perfectly with `dj.choices.Choices`.
* include permissions per field checking using `ralph.lib.permissions.api.PermissionsPerFieldSerializerMixin` - only fields to which user has access will be returned. This field also handle view-only permission as read-only field.
* include permission validation on object level for related fields - if related field model use permissions for object, then only objects to which user has access could be selected/displayed in related field.
* validate data using model's clean validation (set `_validate_using_model_clean` to `False` in your save seriazlier to turn this off)

### `RalphAPIViewSet`
* default serializer for save actions (POST, PUT, PATCH) in which every relation will be serialized using `rest_framework.serializers.PrimaryKeyRelatedField` (so user should specify object PK in relation field). This serializer could be overwritten using `save_serializer_class` attribute in `RalphAPIViewSet`.
* include `ralph.api.utils.QuerysetRelatedMixin` which can easily handle select_related and prefetch_related on queryset. By default select_related is fill with related admin site list_select_related value.
* include `ralph.api.viewsets.AdminSearchFieldsMixin` thanks to which search fields will be by default taken from related admin site.
* include `ralph.api.permissions.RalphPermission`, which check if user is properly authenticated (through `IsAuthenticated`), user has access to object (through `ObjectPermissionsMixin`) and user has proper Django admin permissions (`add_*`, `change_*`, `delete_*`) requested model.

#### Filter backends
By default `RalphAPIViewSet` use the following filter backends:
* `rest_framework.filters.DjangoFilterBackend` - provides basic filtering for Django model - in `RalphAPIViewSet` (through `AdminSearchFieldsMixin`) filter fields are associated with model's admin.
* `ralph.lib.permissions.api.PermissionsForObjectFilter` - limit result only to object for which user has permission at least to view.
* `rest_framework.filters.OrderingFilter` - order queryset using `order` url param.
* `ralph.api.filters.ExtendedFiltersBackend` - allows to filter for multiple fields using single query param - it's usefull especially for polymorphic models. To use extended filters define `extended_filter_fields` in your view, ex. `extended_filter_fields = {'name': ['asset__hostname', ip__address', 'cloudhost__hostname']` - this filter will allow you to search using `name` query param and it will be resolved to compound search (using OR operator) for fields `asset__hostname`, `ip__address` or `cloudhost__hostname` (ex. `<URL>?name=abc` will result in search `Q(asset__hostname=abc) | Q(ip__address=abc) | Q(cloudhost__hostname=abc)`).
* `ralph.api.filters.LookupFilterBackend` - filter by lookups (using Django's `__` convention) in query params, ex. `<URL>?barcode__startswit=123` or `<URL>?invoice_date__lte=2015-01-01`.
* `ralph.api.filters.TagsFilterBackend` - Filter queryset by tags. Multiple tags could be specified in url query: `<URL>?tag=abc&tag=def&tag=123`.

> Note that polymorphic models (api resources) by default support lookup filters and extended filters, so you could call compound query on your polymorphic-root model, ex. `<URL>/base-objects/?name__startswith=abc`, which will be resolved to query, checking if one of fields defined in `extended_filter_fields` (in above example `asset__hostname`, `ip__address` or `cloudhost__hostname`) startswith `abc`.
