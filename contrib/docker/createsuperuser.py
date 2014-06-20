
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ralph.settings")

#from django.core.management import setup_environ
#from django.conf import settings
#import settings
#setup_environ(settings)

from django.contrib.auth.models import User

u = User.objects.get(username='ralph')
u.set_password('ralph')
u.is_superuser = True
u.is_staff = True
u.save()
