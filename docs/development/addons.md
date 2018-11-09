# Extending Ralph

Ralph NG is easy to extend, for example providing custom tabs into the Asset review context or override some methods.

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

## Override methods (hooks)
You can change behaviour some parts of Ralph by overriding exposed methods. It all comes down to add a new entry point in your package (entry in ``setup.py``) and configure by changing settings (by exporting a environment variable) for appropriate entry. For your convience, we create management command for checking current configuration for hooks. You can run it by following command:

```bash
$ dev_ralph show_hooks_configuration

Hooks:
    back_office.transition_action.email_context:
            default (active)
            foo_method
            bar_method
```

Where `foo_method` and `bar_method` are defined in `setup.py` in section `entry_points`:

```python3
from setuptools import setup, find_packages

setup(
    name='my_package',
    ...

    entry_points={
        'back_office.transition_action.email_context': [
            'foo_method = my_package.helpers:get_foo_context',
            'bar_method = my_package.helpers:get_bar_context',
        ]
    },
    ...
)

```


### Available hooks
| Name                                          | Description                                         | Parameters                | Return value                                                  |
| --------------------------------------------- | --------------------------------------------------- | ------------------------- | ------------------------------------------------------------- |
| `back_office.transition_action.email_context` | returns subject and body based on transition's name | `transition_name: str`    | `EmailContext` (`namedtuple`) with fields ``subject`` ``body``|

### Configuration
To change hook please define environment variable named like hook's name but it's upper case and dots are replaced by `_`, for instance, hook with name `back_office.transition_action.email_context` you can configure by export `BACK_OFFICE_TRANSITION_ACTION_EMAIL_CONTEXT` to your environment where value is one of entries point name. See example below.

```bash
$ HOOKS_BACK_OFFICE_TRANSITION_ACTION_EMAIL_CONTEXT=foo_method dev_ralph show_hooks_configuration

Hooks:
    back_office.transition_action.email_context:
            default
            foo_method (active)
            bar_method
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


### Additional filters options:

#### Filter title

```python3
class ServerRoom(models.Model):
    data_center = models.ForeignKey(DataCenter, verbose_name=_("data center"))
    data_center._filter_title = _('data center')
```

If `_filter_title` is attached to field, filter will display the entered name on list, rather than getting it from the model's field.


#### Autocomplete

```python3
class ServerRoom(models.Model):
    data_center = models.ForeignKey(DataCenter, verbose_name=_("data center"))
    data_center._autocomplete = False
```

For each field ForeignKey autocomplete widget is used by default. If you want this to be a select field set _autocomplete to False.
