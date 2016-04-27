# -*- encoding: utf-8 -*-
from setuptools import setup

setup(
    name='dhcp_agent',
    version='0.0.1',
    author='Grupa Allegro Sp. z o.o. and Contributors',
    author_email='pylabs@allegro.pl',
    platforms=['any'],
    license='Apache Software License v2.0',
    py_modules=[
        'dhcp_agent',
    ],
    entry_points={
        'console_scripts': [
            'ralph-dhcp-agent = dhcp_agent:main',
        ],
    }
)
