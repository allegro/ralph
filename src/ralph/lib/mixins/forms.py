# -*- coding: utf-8 -*-
from django import forms


class RequestFormMixin(object):
    """
    Form which has access to request and user
    """
    def __init__(self, *args, **kwargs):
        if not hasattr(self, '_request') or not self._request:
            self._request = kwargs.pop('_request', None)
        if not hasattr(self, '_user'):
            self._user = kwargs.pop(
                '_user',
                self._request.user if self._request else None
            )
        super().__init__(*args, **kwargs)


class RequestModelForm(RequestFormMixin, forms.ModelForm):
    pass
