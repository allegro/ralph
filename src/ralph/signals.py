from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver


# TODO(mkurek): make this working as a decorator, example:
# @post_commit(MyModel)
# def my_handler(instance):
#    ...
def post_commit(func, model, signal=post_save, single_call=True):
    """
    Post commit signal for specific model.

    It's better than Django's post_save, because:
    * it handles transaction rollback (transaction could be rolled back
      after calling post_save)
    * it handles M2M relations (post_save is (usually) called when main model
      is saved, before related M2M instances are saved)

    Writing tests:
        Remember to make your TestCase inheriting from one of:
            - TransactionTestCase (Django)
            - APITransactionTestCase (Django Rest Framework)
        Unless `on_commit` signal won't be called.

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
            called_already_attr = "_" + func.__name__ + "_called"
            if not (getattr(instance, called_already_attr, False) and single_call):
                func(instance)
                setattr(instance, called_already_attr, True)

        transaction.on_commit(wrapper)
