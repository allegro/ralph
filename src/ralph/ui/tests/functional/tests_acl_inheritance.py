# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase


class ACLInheritanceTest(TestCase):

    def test_all_views_inherit_acls(self):
        from ralph import urls
        from ralph.ui.views.common import ACLGateway

        excluded_urls = [
            '^api/',
            '^admin/',
            '^admin/lookups/',
            '^rq/',
        ]

        # A list of callbacks that are functions (except 'AddVM'), and
        # therefore they do not inherit from ACLGateway class.
        #
        # The idea here is to maintain such list in one place, examine its
        # members one by one, and eventually remove them (by commenting out)
        # if they don't need any ACL mechanisms or if it's possible to enforce
        # such mechanisms in a different way.
        excluded_callbacks = [
            ('serve', 'django.views.static'),
            ('serve', 'django.views.static'),
            ('login', 'django.contrib.auth.views'),
            ('logout', 'django.contrib.auth.views'),
            ('redirect_to', 'django.views.generic.simple'),

            ('show_ventures', 'ralph.business.views'),
            ('show_ventures', 'ralph.business.views'),

            ('servertree', 'ralph.integration.views'),
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
            ('preboot_type_view', 'ralph.deployment.views'),
            ('preboot_complete_view', 'ralph.deployment.views'),
            ('puppet_classifier', 'ralph.deployment.views'),
        ]

        # constructing a list of URL patterns for testing
        urlpatterns_to_test = []
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
                        urlpatterns_to_test.extend(
                            included_urlpattern.url_patterns
                        )
                    else:
                        urlpatterns_to_test.append(included_urlpattern)
                continue
            else:
                urlpatterns_to_test.append(urlpattern)

        # actual testing
        for urlpattern in urlpatterns_to_test:
            class_name = urlpattern.callback.__name__
            module_name = urlpattern.callback.__module__
            if (class_name, module_name) in excluded_callbacks:
                continue
            imported_module = __import__(module_name, fromlist=[class_name])
            found_class = getattr(imported_module, class_name)
            msg = "View '{}' doesn't inherit from ACLGateway class".format(
                '.'.join([module_name, class_name])
            )
            self.assertIn(ACLGateway, found_class.__mro__, msg)
