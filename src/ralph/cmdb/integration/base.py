#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
from django.core.mail import mail_admins

from ralph.cmdb import models as db


logger = logging.getLogger(__name__)

class BaseImporter(object):
    """
    Base class for importer plugins
    """
    notify_mail=False
    matched=0
    not_matched=0

    def handle_duplicate_name(self, name):
        pass

    def do_summary(self):
        mail_admins(
                'Integration statistics',
                '''
                    Report:<br>
                    <hr>
                    statistics: items matched: %(matched)d | items not matched %(not_matched)d<br>
                ''' % dict(
                    matched=self.matched,
                    not_matched=self.not_matched,
                ),
                fail_silently=True,
                html_message=True,
        )


    def handle_integration_error(self, classname, methodname, e):
        logger.error("Integration error. %(classname)s %(methodname)s : %(error)s" %
        dict(
            classname=classname,
            methodname=methodname,
            error=e,
        ))
        if self.notify_mail:
            mail_admins(
                        'Integration errors',
                        '''
                            Errors in %(class_name).%(method_name)
                            Error message: %(error_message)s <br>

                        ''' % dict(
                            class_name=classname,
                            method_name=methodname,
                            error_message=unicode(e),

                        ),
                        fail_silently=True,
                        html_message=True,
            )

    def get_ci_by_name(self, name, type=None):
        ci = db.CI.objects.filter(name=name).all()
        if len(ci) == 1:
            return ci[0]
        elif len(ci)>1:
            self.handle_duplicate_name(name)
            return None
        else:
            return None


