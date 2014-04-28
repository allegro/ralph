#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

from tastypie.authorization import Authorization
from tastypie.exceptions import Unauthorized


NO_ACCESS_MSG = _('Access Denied')


class RalphAuthorization(Authorization):

    def __init__(self, required_perms, *args, **kwargs):
        super(RalphAuthorization, self).__init__(*args, **kwargs)
        self.required_perms = required_perms

    def authorized(self, user):
        user = User.objects.get(username=user.username).get_profile()
        for perm in self.required_perms:
            if not user.has_perm(perm):
                raise Unauthorized(NO_ACCESS_MSG)
        return True

    def read_list(self, object_list, bundle):
        if self.authorized(bundle.request.user):
            return object_list
