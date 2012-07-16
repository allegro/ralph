# -*- encoding: utf-8 -*-

import os
import sys
from setuptools import setup, find_packages

assert sys.version_info >= (2, 7), "Python 2.7+ required."

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as ld_file:
    long_description = ld_file.read()

from doc.conf import release

setup (
    name = 'ralph',
    version = release,
    author = 'Grupa Allegro Sp. z o.o. and Contributors',
    author_email = 'it-ralph-dev@allegro.pl',
    description = "Ralph, the responsible leader of the children in `Lord " \
                  "of the Flies`.",
    long_description = long_description,
    url = 'http://ralph.allegrogroup.com/',
    keywords = '',
    platforms = ['any'],
    license = 'Apache Software License v2.0',
    packages = find_packages('src'),
    include_package_data = True,
    package_dir = {'':'src'},
    zip_safe = False, # because templates are loaded from file path
    install_requires = [
        'django-ajax-selects==1.2.4',
        'django-bob==1.0.1dev2',
        'django-celery==3.0.1',
        'django-powerdns==0.2',
        'django-tastypie==0.9.11',
        'django==1.4',
        'dnspython==1.10.0',
        'fugue-icons==3.4.4',
        'gunicorn==0.14.5',
        'ipaddr==2.1.7',
        'iscconf==1.0.0dev3',
        'jpath==1.2',
        'lck.django==0.7.12',
        'lxml>=2.3.3',
        'mock==0.8.0',
        'MySQL-python==1.2.3',
        'ping==0.2',
        'pysnmp==4.2.2',
        'PyYAML==3.10',
        'pyzabbix==0.1',
        'RestKit==2.0',
        'setproctitle==1.1.6',
        'South==0.7.5',
        'splunk-sdk==0.8.0',
        'SQLAlchemy==0.7.8',
        'ssh==1.7.14',
        'pytz',
        ],
    entry_points={
        'console_scripts': [
            'pping = ralph.util.network:ping_main',
            'cmdb_sync = ralph.cmdb.importer:importer_main',
            'cmdb_integration = ralph.cmdb.integration.sync:integrate_main',
        ],
    },
    classifiers = [
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows :: Windows NT/2000',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 2 :: Only',
        'Topic :: Internet :: WWW/HTTP',
        ]
    )
