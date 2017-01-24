from django.db import connection
from django.db.models.signals import post_save
from django.dispatch import receiver


# TODO: make this working as a decorator, example:
# @post_commit(MyModel)
# def my_handler(instance):
#    ...
def post_commit(func, model, signal=post_save, prevent_multiple_calls=True):
    """
    Post commit signal for specific model.

    It's better than Django's post_save, because:
    * it handles transaction rollback (transaction could be rolled back
      after calling post_save)
    * it handles M2M relations (post_save is (usually) called when main model
      is saved, before related M2M instances are saved)

    Requirements:
    * you have to use database supporting transactions (ex. MySQL)
    * you have to use django-transaction-hooks
      (https://github.com/carljm/django-transaction-hooks) for Django<=1.8
      (it was merged into Django 1.9)

    Notice that this feature will work whether or not you're using transactions
    in your code. Possible scenarios are as follows:
    * `ATOMIC_REQUESTS` is set to True in settings - then every request is
      wrapped in transaction - at the end of processing each (saving) request,
      this hook will be processed (for models which were saved)
    * view is decorated using `transaction.atomic` - at the end of processing
      the view, this hook will be called (if any of registered models was saved)
    * if transaction is not started for current request, then this hook will
      behave as post_save (will be called immediately)
    """
    @receiver(signal, sender=model, weak=False)
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
