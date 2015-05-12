Signals
=======

.. module:: ralph_assets.signals
   :synopsis: Signals sent by the ralph_assets module.

The :mod:`ralph_assets.signals` module defines a set of signals sent by the ralph_assets.

Transition signals
------------------
Use this type of signals if you want send email or something else after some transition.

post_transition
~~~~~~~~~~~~~~~
Arguments sent with this signal:

``user``
    A user which run transition.

``assets``
    A list of assets which undergo transition.

``transition``
    A transition object.


Form signals
------------
Signals related with form.

post_customize_fields
~~~~~~~~~~~~~~~~~~~~~
This signal is useful if you want customize form from external application. Arguments sent with this signal:

``sender``
    The form instance.

``mode``
    A string. Possible values: ``bo`` or ``back_office``.

For example::

    from django import forms

    from ralph_assets.signals import post_customize_fields


    @receiver(post_customize_fields)
    def my_awesome_customizer(sender, mode, **kwargs):
        if(len(sender['barcode'].value) < 50)
            sender.fields['barcode'].widget = forms.widgets.TextInput()


