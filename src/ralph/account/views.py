#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import urlparse

from bob.menu import MenuItem, MenuHeader
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.sites.models import get_current_site
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.template.response import TemplateResponse


from ralph.account.forms import UserHomePageForm
from ralph.account.models import get_user_home_page, Preference, UserPreference
from ralph.ui.views.common import Base


class BaseUser(Base):
    template_name = 'base.html'

    def get_sidebar_items(self):
                preferences = (
                    (
                        reverse('user_home_page', args=[]),
                        _('Home Page'),
                        'fugue-home'
                    ),
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


class BaseUserPreferenceEdit(BaseUser):
    template_name = 'preference.html'
    Form = None
    preference_type = None
    header = None

    def get(self, *args, **kwargs):
        instance, created = UserPreference.objects.get_or_create(
            preference=self.preference_type,
            user=self.request.user,
        )
        self.form = self.Form(instance=instance)
        return super(BaseUserPreferenceEdit, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
            instance, created = UserPreference.objects.get_or_create(
                preference=self.preference_type,
                user=self.request.user,
            )
            self.form = self.Form(self.request.POST, instance=instance)
            if self.form.is_valid():
                self.form.save()
                messages.success(self.request, _("Changes saved."))
            return super(BaseUserPreferenceEdit, self).get(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        ret = super(BaseUserPreferenceEdit, self).get_context_data(**kwargs)
        ret.update({
            'section': _('User Preference - ') + self.header,
            'form': self.form,
            'action_url': reverse('user_home_page', args=[]),
            'header': self.header
        })
        return ret


class UserHomePageEdit(BaseUserPreferenceEdit):
    Form = UserHomePageForm
    preference_type = Preference.home_page.id
    header = _('Home Page')


@sensitive_post_parameters()
@csrf_protect
@never_cache
def login(request, template_name='registration/login.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          authentication_form=AuthenticationForm,
          current_app=None, extra_context=None):
    """
    Displays the login form and handles the login action.
    """
    redirect_to = request.REQUEST.get(redirect_field_name, '')
    if request.method == "POST":
        form = authentication_form(data=request.POST)
        if form.is_valid():
            netloc = urlparse.urlparse(redirect_to)[1]
            # Use default setting if redirect_to is empty
            if redirect_to == reverse('search'):
                user_redirect = get_user_home_page(
                    request.POST.get('username')
                )
                if user_redirect:
                    redirect_to = user_redirect
            if not redirect_to:
                redirect_to = settings.LOGIN_REDIRECT_URL
            # Heavier security check -- don't allow redirection to a different
            # host.
            elif netloc and netloc != request.get_host():
                redirect_to = settings.LOGIN_REDIRECT_URL
            # Okay, security checks complete. Log the user in.
            auth_login(request, form.get_user())
            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()
            return HttpResponseRedirect(redirect_to)
    else:
        form = authentication_form(request)
    request.session.set_test_cookie()
    current_site = get_current_site(request)
    context = {
        'form': form,
        redirect_field_name: redirect_to,
        'site': current_site,
        'site_name': current_site.name,
    }
    if extra_context is not None:
        context.update(extra_context)
    return TemplateResponse(
        request, template_name, context, current_app=current_app
    )
