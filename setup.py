# -*- encoding: utf-8 -*-

import os
import sys
from setuptools import setup, find_packages

assert sys.version_info >= (2, 7), 'Python 2.7+ required.'


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='ralph',
    version='3.0.0',
    author='Grupa Allegro Sp. z o.o. and Contributors',
    author_email='pylabs@allegro.pl',
    description="Assets management module for Ralph",
    long_description='\n'.join([read('README'), read('CHANGES')]),
    url='http://ralph.allegrogroup.com/',
    keywords='',
    platforms=['any'],
    license='Apache Software License v2.0',
    packages=find_packages('src'),
    include_package_data=True,
    package_dir={'': 'src'},
    zip_safe=False,  # because templates are loaded from file path
    install_requires=read('requirements/base.txt').split('\n'),
    extras_require={
        'devel': read('requirements/dev.txt').split('\n'),
        'test': read('requirements/test.txt').split('\n'),
    },
    entry_points={
        'console_scripts': [
            'ralph = ralph.__main__:main',
            'dev_ralph = ralph.__main__:dev',
            'test_ralph = ralph.__main__:test',
        ],
    },
    classifiers=[
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
