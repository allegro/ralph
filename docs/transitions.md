# Transitions
The transition change state (e.g. status) of object from one to another - that's helps in product lifecycle management. For each object (asset, support, licence) you can define some workflow (set of transitions) and provide special actions for each transition.

## Adding new action
You can easliy add new action by add method to your class and decorating with ``@transition_action``. For exmple:

```django
class Order(models.Model, metaclass=TransitionWorkflowBase):
    status = TransitionField(
        default=OrderStatus.new.id,
        choices=OrderStatus(),
    )

    @classmethod
    @transition_action
    def pack(cls, instances, request, **kwargs):
        notify_buyer('We pack your order for you.')

    @classmethod
    @transition_action
    def go_to_post_office(cls, instances, request, **kwargs):
        notify_buyer('We send your order to you.')
```

Now actions are available in admin panel when you can specify your workflow.

![Add transition](img/add_transitions.png)

If your action required extra parameters to execute you can add fields:
```django
from django import forms

ALLOW_COMMENT = True

    ...
    @classmethod
    @transition_action(
        form_fields = {
            'comment': {
                'field': forms.CharField(),
                'condition': lambda obj: (obj.status > 2) and ALLOW_COMMENT
            }
        }
    )
    def pack(cls, instances, request, **kwargs):
        notify_buyer(
            'We pack your order for you.',
            pickers_comment=kwargs['comment'],
        )
```

![Extra params](img/extra_params.png)

Allowed params for field::
    ``field`` - standard form field, e.g. from ``django.forms``,
    ``condition`` - function wich accept one parameter and return boolean, when condition have be met the field will be shown.

Set ``return_attachment`` to ``True`` if action return attachment (e.g.: PDF document).
