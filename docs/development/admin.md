# Ralph Admin

Ralph Admin class (`ralph.admin.mixins.RalphAdmin`) is built on top of regular Django Admin and has bunch of extending features. Some of them are listed below.

## Import-Export

Ralph Admin has built-in support for importing and exporting objects (using [django-import-export](https://github.com/django-import-export/django-import-export)). Possible configuration:

### Resource class

Define `resouce_class` in your Admin to specify django-import-export's resource class used to handle importing and exporting of this model.

Example:
```
class SupportAdmin(RalphAdmin):
    ...
    resource_class = resources.SupportResource
    ...
```

### Export queryset

Define `_export_queryset_manager` attribute in your Admin to specify which manager will be used to handle export queries. This should be string with model's attribute name for proper manager.

Example:
```
class SupportAdmin(RalphAdmin):
    ...
    _export_queryset_manager = 'objects_with_related'
    ...
```

> Export in Admin by default use `get_queryset` from Django's admin to properly handle all filters etc. During export from Admin, `get_queryset` defined in your Resource is not used, but it is a good practice, to point them to the same objects manager.

### Fetching related objects

Ralph Admin, by default, [select](https://docs.djangoproject.com/en/1.8/ref/models/querysets/#select-related) and [prefetch](https://docs.djangoproject.com/en/1.8/ref/models/querysets/#prefetch-related) all related objects that are defined in Resource's Meta.
