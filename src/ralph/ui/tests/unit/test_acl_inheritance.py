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
        ]

        # A list of callbacks that are excluded from permissions checks via
        # 'ACLGateway' class / 'ralph_permission' decorator.
        # Entries commented out are the callbacks decorated with
        # 'ralph_permission' manually (i.e. not inheriting 'ACLGateway' class),
        # but we leave them here to keep track of such changes.
        self.excluded_callbacks = [
            ('serve', 'django.views.static'),
            ('login', 'django.contrib.auth.views'),
            ('logout', 'django.contrib.auth.views'),
            ('redirect_to', 'django.views.generic.simple'),

            ('stats', 'django_rq.views'),  # 'django_rq' is a separate app ('^rq/' urls)
            ('jobs', 'django_rq.views'),
            ('job_detail', 'django_rq.views'),
            ('delete_job', 'django_rq.views'),
            ('requeue_job_view', 'django_rq.views'),

            ('show_ventures', 'ralph.business.views'),

            ('servertree', 'ralph.integration.views'),

            ('logout', 'ralph.ui.views'),
            ('AddVM', 'ralph.ui.views.deploy'),  # checks permissions on its own
            ('typeahead_roles', 'ralph.ui.views'),
            ('unlock_field', 'ralph.ui.views'),

            # ('dhcp_synch', 'ralph.dnsedit.views'),
            # ('dhcp_config_entries', 'ralph.dnsedit.views'),
            # ('dhcp_config_networks', 'ralph.dnsedit.views'),
            # ('dhcp_config_head', 'ralph.dnsedit.views'),

            ('get_ajax', 'ralph.cmdb.views_changes'),  # static methods in Dashboard / TimeLine
            ('commit_hook', 'ralph.cmdb.rest.rest'),
            ('notify_puppet_agent', 'ralph.cmdb.rest.rest'),

            ('preboot_type_view', 'ralph.deployment.views'),
            ('preboot_raw_view', 'ralph.deployment.views'),
            ('preboot_complete_view', 'ralph.deployment.views'),
            # ('puppet_classifier', 'ralph.deployment.views'),
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
            msg = "Class '{}' does not inherit from 'ACLGateway' class.".format(found_callback)
            self.assertTrue(issubclass(found_callback, ACLGateway), msg)


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
            msg = "Function '{}' is not decorated with '@ralph_permission'.".format(
                '.'.join((module_name, found_callback.func_name))
            )
            self.assertEqual(decorator_name, 'ralph_permission', msg)


    # slightly simplier method combining the two tests above - left here
    # commented out for future reference
    # def test_callback_uses_ralph_permission_decorator(self):
    #     for urlpattern in self.urlpatterns_to_test:
    #         callback = urlpattern.callback
    #         callback_name = urlpattern.callback.__name__
    #         module_name = urlpattern.callback.__module__
    #         if (callback_name, module_name) in self.excluded_callbacks:
    #             continue
    #         decorator_name = getattr(callback, 'decorated_with', None)
    #         msg = "Callback '{}' does not use '@ralph_permission' decorator.".format(
    #             '.'.join((module_name, callback_name))
    #         )
    #         self.assertEqual(decorator_name, 'ralph_permission', msg)
