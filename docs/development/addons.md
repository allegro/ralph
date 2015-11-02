# Extending Ralph

Ralph NG is easy to extend, for example providing custom tabs into the Asset review context.

Note: We encourage the developers to contribute new functions and integrations! Please read [this document](../CONTRIBUTING.md) for more information.


## Extending the Detail View

Providing custom sub-page for asset detail view is the most convenient way to integrate content from another Django app into a Ralph admin page. All registred views will be represented by tab on ralph site. Notice that single view class cannot be reused in multiple admin sites.

You must write your own class view and template. There are two possibilities to add extra view: by decorator and by class' attribute.

### Your view

It must be normal view (CBV) inherited from ``RalphListView`` or ``RalphDetailView`` (it depends on view purpose).

#### RalphListView

This class is dedicated for listing view.

#### RalphDetailView

This class is dedicated for details view. Instance of class provides additional attributes:

- ``model`` - actual model class,
- ``object`` - concrete object, fetched from ``model`` and ``id``.

You have access from template to ``object``.

#### RalphDetailViewAdmin

If you want display standard admin model as tab, please use this class. Class accept two basic attributes from ``django.contrib.admin.ModelAdmin``:

- ``inlines``,
- ``fieldsets``.

Example:
```django
class NetworkInline(TabularInline):
    model = IPAddress


class NetworkView(RalphDetailViewAdmin):
    icon = 'chain'
    name = 'network'
    label = 'Network'
    url_name = 'network'

    inlines = [NetworkInline]
```

### Template

Each templates must extends from ``BASE_TEMPLATE``.

Basic template:
```django
{% extends BASE_TEMPLATE %}

{% block content %}
    {{ var }}
{% endblock %}
```

Your templates must be placed in one of predefined path:

- ``model/name.html``
- ``app_label/model/name.html``

Where:

- ``app_label`` - is ``app_label`` extracted from ``model``,
- ``model`` - lowercase name of ``model``,
- ``name`` - name of view gets from view's instance.

### Register view via class atrribiute

**Note:** Use this method if you developing directly in Ralph.

in ``admin.py``:
```python3
from ralph.admin import RalphAdmin, register
from ralph.admin.views import RalphDetailView
from ralph.back_office.models import Warehouse


class ExtraView(RalphDetailView):
    name = 'extra_list'
    label = 'Extra Detail View'


@register(Warehouse)
class WarehouseAdmin(RalphAdmin):
    change_views = [ExtraView]
```

### Register view via decorator

**Note:** This method is recommended for external application.

somewhere in your application:
```python3
from ralph.admin.decorators import register_extra_view
from ralph.admin.views import RalphDetailView
from ralph.back_office.models import Warehouse


@register_extra_view(Warehouse, register_extra_view.CHANGE)
class ExtraView(RalphDetailView):
    name = 'extra_details'
    label = 'Extra Detail View'
```


## Using advanced search filters

You could easily define your own advanced search filters (to search by text, date etc). Available filters are:

* BooleanFilter (`ralph.admin.filters.BooleanFilter`)
* ChoicesFilter (`ralph.admin.filters.ChoicesFilter`)
* DateFilter (`ralph.admin.filters.DateFilter`)
* TextFilter (`ralph.admin.filters.TextFilter`)

To use filter define your class, where you specify field title and parameter
against which result will be filtered:

    class BarcodeFilter(TextFilter):
        title = _('Barcode')
        parameter_name = 'barcode'

Then simply add this class to `list_filter` attribute in your admin class definition:

    class MyAdmin(RalphAdmin):
        list_filter = [BarcodeFilter]

To use `ChoicesFilter` you need to specify one additional param: `choices_list`, which should be list of available choices to select from (`dj.choices.Choices` instance is recommended here).
