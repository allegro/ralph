from django.dispatch import Signal

# This signal is sent at the end of CustomFieldValueSaveSerializer's `create()`
# method.
api_post_create = Signal(providing_args=['instance'])

# This signal is sent at the end of CustomFieldValueSaveSerializer's `update()`
# method.
api_post_update = Signal(providing_args=['instance'])
