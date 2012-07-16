import site
site.addsitedir('/home/ralph/lib/python2.7/site-packages')

import os
import sys

# enables simplistic logging using "print" statements
sys.stdout = sys.__stderr__
sys.stderr = sys.__stderr__
sys.stdin = sys.__stdin__

os.environ['DJANGO_SETTINGS_MODULE'] = 'ralph.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
