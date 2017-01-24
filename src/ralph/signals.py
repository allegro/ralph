from django.db import connection
from django.db.models.signals import post_save
from django.dispatch import receiver


def post_commit(func, model, prevent_multiple_calls=True):
    """
    TODO
    """
    @receiver(post_save, sender=model, weak=False)
    def wrap(sender, instance, **kwargs):
        def wrapper():
            # prevent from calling the same func multiple times for single
            # instance
            called_attr = '_' + func.__name__ + '_called'
            if (
                not getattr(instance, called_attr, False) or
                not prevent_multiple_calls
            ):
                func(instance)
                setattr(instance, called_attr, True)

        # TODO: replace connection by transaction after upgrading to Django 1.9
        connection.on_commit(wrapper)
