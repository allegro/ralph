# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import inspect

from django.test import TestCase

from ralph.ui.views.common import ACLGateway

class ACLInheritanceTest(TestCase):

    def setUp(self):
        from ralph import urls
        excluded_urls = [
            '^api/',
            '^admin/',
            '^admin/lookups/',
            '^rq/',
        ]

        # A list of callbacks that are excluded from permissions checks via
        # ralph_permission decorator / ACLGateway class. The idea here is to
        # maintain such list in one place, examine its members one by one,
        # and eventually remove them (by commenting out) if they don't need
        # any ACL mechanisms or if it's possible to enforce such mechanisms
        # in a different way.
        self.excluded_callbacks = [
            ('serve', 'django.views.static'),
            ('login', 'django.contrib.auth.views'),
            ('logout', 'django.contrib.auth.views'),
            ('redirect_to', 'django.views.generic.simple'),

            ('show_ventures', 'ralph.business.views'),

            ('servertree', 'ralph.integration.views'),

            ('logout', 'ralph.ui.views'),
            ('typeahead_roles', 'ralph.ui.views'),
            ('unlock_field', 'ralph.ui.views'),
            ('AddVM', 'ralph.ui.views.deploy'),

            ('dhcp_synch', 'ralph.dnsedit.views'),
            ('dhcp_config_entries', 'ralph.dnsedit.views'),
            ('dhcp_config_networks', 'ralph.dnsedit.views'),
            ('dhcp_config_head', 'ralph.dnsedit.views'),

            ('commit_hook', 'ralph.cmdb.rest.rest'),
            ('notify_puppet_agent', 'ralph.cmdb.rest.rest'),
            ('get_ajax', 'ralph.cmdb.views_changes'),

            ('preboot_type_view', 'ralph.deployment.views'),
            ('preboot_raw_view', 'ralph.deployment.views'),
            ('preboot_complete_view', 'ralph.deployment.views'),
            ('puppet_classifier', 'ralph.deployment.views'),
        ]

        # constructing a list of URL patterns for testing
        self.urlpatterns_to_test = []
        for urlpattern in urls.urlpatterns:
            if urlpattern._regex in excluded_urls:
                continue
            if hasattr(urlpattern.callback, 'func_name'):
                if urlpattern.callback.func_name in (
                    'RedirectView',
                    'VhostRedirectView',
                ):
                    continue
            if hasattr(urlpattern, 'url_patterns'):
                for included_urlpattern in urlpattern.url_patterns:
                    # included urlpattern can include other patterns too
                    if hasattr(included_urlpattern, 'url_patterns'):
                        self.urlpatterns_to_test.extend(
                            included_urlpattern.url_patterns
                        )
                    else:
                        self.urlpatterns_to_test.append(included_urlpattern)
                continue
            else:
                self.urlpatterns_to_test.append(urlpattern)


    def test_class_based_views_inherit_from_acl_gateway_class(self):
        for urlpattern in self.urlpatterns_to_test:
            callback_name = urlpattern.callback.__name__
            module_name = urlpattern.callback.__module__
            if (callback_name, module_name) in self.excluded_callbacks:
                continue
            imported_module = __import__(module_name, fromlist=[callback_name])
            found_callback = getattr(imported_module, callback_name)
            if not inspect.isclass(found_callback):
                continue
            self.assertTrue(issubclass(found_callback, ACLGateway))


    def test_function_based_views_are_decorated_with_ralph_permission(self):
        for urlpattern in self.urlpatterns_to_test:
            callback_name = urlpattern.callback.__name__
            module_name = urlpattern.callback.__module__
            if (callback_name, module_name) in self.excluded_callbacks:
                continue
            imported_module = __import__(module_name, fromlist=[callback_name])
            found_callback = getattr(imported_module, callback_name)
            if not inspect.isfunction(found_callback):
                continue
            decorator_name = getattr(found_callback, 'decorated_with', None)
            self.assertEqual(decorator_name, 'ralph_permission')
