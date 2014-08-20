# -*- encoding: utf-8 -*-

import os
import sys
from setuptools import setup, find_packages

assert sys.version_info >= (2, 7), "Python 2.7+ required."

current_dir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(current_dir, 'README.rst')) as readme_file:
    with open(os.path.join(current_dir, 'badges.rst')) as badges_file:
        long_description = readme_file.read() + '\n' + badges_file.read()

sys.path.insert(0, current_dir + os.sep + 'src')
from ralph import VERSION
release = ".".join(str(num) for num in VERSION)

setup(
    name='ralph',
    version=release,
    author='Grupa Allegro Sp. z o.o. and Contributors',
    author_email='pylabs@allegro.pl',
    description="Ralph is a full-featured Asset Management, "
    "DCIM and CMDB system for data center nad backoffice areas.",
    long_description=long_description,
    url='http://ralph.allegrogroup.com/',
    keywords='',
    platforms=['any'],
    license='Apache Software License v2.0',
    packages=find_packages('src'),
    include_package_data=True,
    package_dir={'': 'src'},
    zip_safe=False,  # because templates are loaded from file path
    install_requires=[
        'bob-ajax-selects==1.4.1',
        'django-bob==1.8.1',
        'django-powerdns-dnssec==0.9.3',
        'django-tastypie==0.9.16',
        'django-rq==0.4.5',
        'django==1.4.13',
        'django-pluggable-apps==1.2',
        'django-redis-cache==0.13.0',
        'dnspython==1.11.0',
        'factory-boy==2.3.1',
        'feedparser==5.1.2',
        'fugue-icons==3.5.3',
        'gunicorn==0.14.6',
        'ipaddr==2.1.7',
        'iscconf==1.0.0dev9',
        'jpath==1.2',
        'lck.django==0.8.10',
        'lxml==2.3.5',
        'defusedxml==0.4.1',
        'mock==0.8.0',
        'MySQL-python==1.2.3',
        'paramiko==1.9.0',
        'ping==0.2',
        'pysnmp==4.2.2',
        'PyYAML==3.10',
        'python-graph-core==1.8.2',
        'pytz==2013b',
        'pyzabbix>=0.1',
        'requests>=0.14.2',
        'RestKit==4.2.0',
        'rq>=0.3.7',
        'rq-scheduler==0.3.6',
        'setproctitle==1.1.8',
        'South==0.7.6',
        'splunk-sdk==0.8.0',
        'SQLAlchemy==0.7.8',
        'null==0.6.1',
        'xlwt==0.7.4',
        'unidecode==0.04.14',
        'django-discover-runner>=0.4',
        'Pillow==2.4.0',
        'pysphere==0.1.8',
    ],
    entry_points={
        'console_scripts': [
            'pping = ralph.util.network:ping_main',
            'ralph = ralph.__main__:main',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
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
