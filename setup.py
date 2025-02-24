# -*- encoding: utf-8 -*-

import os
import subprocess
import sys

from setuptools import find_packages, setup

assert sys.version_info >= (3, 3), 'Python 3.3+ required.'


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


def get_version():
    script = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 'get_version.sh'
    )
    ver = subprocess.check_output([script], shell=True)
    return ver.decode().strip()


setup(
    name='ralph',
    version=get_version(),
    author='Allegro.pl Sp. z o.o. and Contributors',
    author_email='opensource@allegro.pl',
    description="Advanced Asset Management and DCIM system for data center and back office.",
    long_description=read('README.md'),
    url='http://ralph.allegrogroup.com/',
    keywords='',
    platforms=['any'],
    license='Apache Software License v2.0',
    packages=find_packages('src'),
    include_package_data=True,
    package_dir={'': 'src'},
    zip_safe=False,  # because templates are loaded from file path
    entry_points={
        'console_scripts': [
            'ralph = ralph.__main__:prod',
            'dev_ralph = ralph.__main__:dev',
            'test_ralph = ralph.__main__:test',
            'validate_ralph = ralph.cross_validator.__main__:main',
        ],
        'back_office.transition_action.email_context': [
            'default = ralph.back_office.helpers:get_email_context_for_transition'  # noqa
        ],
        'account.views.get_asset_list_class': [
            'default = ralph.accounts.views:get_asset_list_class'  # noqa
        ],
        'ralph.cloud_sync_processors': [
            'noop=ralph.virtual.processors.noop:endpoint',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: Django',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows :: Windows NT/2000',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
