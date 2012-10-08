# -*- encoding: utf-8 -*-

import os
import sys
from setuptools import setup, find_packages

assert sys.version_info >= (2, 7), "Python 2.7+ required."

current_dir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(current_dir, 'README.rst')) as readme_file:
    with open(os.path.join(current_dir, 'CHANGES.rst')) as changes_file:
        long_description = readme_file.read() + '\n' + changes_file.read()

sys.path.insert(0, current_dir + os.sep + 'src')
from ralph import VERSION
release = ".".join(str(num) for num in VERSION)

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
        'django-bob==1.3.2',
        'django-celery==3.0.10',
        'django-powerdns==0.2',
        'django-tastypie==0.9.11',
        'django==1.4.1',
        'dnspython==1.10.0',
        'feedparser==5.1.2',
        'fugue-icons==3.4.4',
        'gunicorn==0.14.6',
        'ipaddr==2.1.7',
        'iscconf==1.0.0dev3',
        'jira-python==0.12',
        'jpath==1.2',
        'lck.django==0.7.14',
        'lxml==2.3.5',
        'mock==0.8.0',
        'MySQL-python==1.2.3',
        'ping==0.2',
        'pysnmp==4.2.2',
        'PyYAML==3.10',
        'pytz',
        'pyzabbix==0.1',
        'RestKit==2.0',
        'setproctitle==1.1.6',
        'South==0.7.6',
        'splunk-sdk==0.8.0',
        'SQLAlchemy==0.7.8',
        'ssh==1.7.14',
        ],
    entry_points={
        'console_scripts': [
            'pping = ralph.util.network:ping_main',
            'ralph = ralph.__main__:main',
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
