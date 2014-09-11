#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


from bob.menu import MenuItem, MenuHeader
from django import http
from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.template import (
    RequestContext,
    TemplateDoesNotExist,
    loader,
)
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import requires_csrf_token
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView

from pluggableapp import PluggableApp
from ralph.account.forms import UserHomePageForm
from ralph.account.models import (
    Perm,
    Profile,
    ralph_permission,
)
from ralph.ui.views.common import Base


@requires_csrf_token
def HTTP403(request, msg=None, template_name='403.html'):
    """
    A slightly customized version of 'permission_denied' handler taken from
    'django.views.defaults' (added 'REQUEST_PERM_URL' etc.).
    """
    if not msg:
        msg = _("You don't have permission to this resource.")
    try:
        template = loader.get_template(template_name)
    except TemplateDoesNotExist:
        return http.HttpResponseForbidden('<h1>403 Forbidden</h1>')
    context = RequestContext(request, {
        'REQUEST_PERM_URL': getattr(settings, 'REQUEST_PERM_URL', None),
        'msg': msg,
    })
    return http.HttpResponseForbidden(template.render(context))


class BaseUser(Base):
    template_name = 'base.html'
    submodule_name = 'user_preference'
    module_name = 'user_preference'

    def get_sidebar_items(self):
        has_perm = self.request.user.get_profile().has_perm
        preferences = [(
            reverse('user_api_key', args=[]),
            _('API Key'),
            'fugue-key'
        )]
        if has_perm(Perm.has_core_access):
            preferences.insert(
                0,
                (
                    reverse('user_home_page', args=[]),
                    _('Home Page'),
                    'fugue-home'
                )
            )
        sidebar_items = (
            [MenuHeader('Preferences')] +
            [MenuItem(
                label=preference[1],
                fugue_icon=preference[2],
                href=preference[0]
            ) for preference in preferences]
        )

        return sidebar_items

    def get_context_data(self, *args, **kwargs):
        ret = super(BaseUser, self).get_context_data(**kwargs)
        ret.update({
            'sidebar_items': self.get_sidebar_items(),
        })
        return ret


class ApiKey(BaseUser):
    template_name = 'api_key.html'

    def get_context_data(self, *args, **kwargs):
        ret = super(ApiKey, self).get_context_data(*args, **kwargs)
        ret['api_key'] = self.request.user.api_key.key
        return ret


class BaseUserPreferenceEdit(BaseUser):
    template_name = 'preference.html'
    Form = None
    header = None

    @ralph_permission([{
        'perm': Perm.has_core_access,
        'msg': _("You don't have permissions for this resource.")
    }])
    def dispatch(self, *args, **kwargs):
        return super(TemplateView, self).dispatch(*args, **kwargs)

    def get(self, *args, **kwargs):
        instance = Profile.objects.get(
            user_id=self.request.user.id,
        )
        self.form = self.Form(instance=instance)
        return super(BaseUserPreferenceEdit, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        instance = Profile.objects.get(
            user_id=self.request.user.id,
        )
        self.form = self.Form(self.request.POST, instance=instance)
        if self.form.is_valid():
            self.form.save()
            messages.success(self.request, _("Changes saved."))
        return super(BaseUserPreferenceEdit, self).get(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        ret = super(BaseUserPreferenceEdit, self).get_context_data(**kwargs)
        ret.update({
            'section': '%s - %s' % (_("User Preference"), self.header),
            'form': self.form,
            'action_url': reverse('user_home_page', args=[]),
            'header': self.header
        })
        return ret


class UserHomePageEdit(BaseUserPreferenceEdit):
    Form = UserHomePageForm
    header = _('Home Page')


class UserHomePage(RedirectView):

    def get(self, request, *args, **kwargs):
        redirect_hierarchy = [
            (Perm.has_scrooge_access, 'ralph_scrooge'),
            (Perm.has_assets_access, 'ralph_assets'),
        ]
        profile = request.user.get_profile()
        for perm_to_module, app_name in redirect_hierarchy:
            if profile.has_perm(perm_to_module):
                try:
                    page_url = PluggableApp.apps[app_name].home_url
                    break
                except KeyError:
                    pass
        else:
            page_url = reverse('search', args=('info', ''))
        return HttpResponseRedirect(page_url)
