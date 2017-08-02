#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Chris Ward <cward@redhat.com>

from setuptools import setup
import sys

if sys.version_info < (3, 6):
    sys.exit('Sorry, Python < 3.6 is not supported')

from comdev import __version__ as VERSION

long_description = '''Community Development support library'''

setup_info = dict(
    # Metadata
    name='comdev',
    version=VERSION,
    license='GPLv3',
    author='Chris Ward',
    author_email='cward@redhat.com',
    description=long_description,
    long_description=long_description,
    # Package info
    packages=['comdev', ],
    install_requires=[
        'babel',
        'click',
        'confuse',
        # 'gdata',  # not py3 compatible
        #'https://github.com/dvska/gdata-python3#egg=gdata'
        # ^^^ must run `python setup.py install` though... develop
        'google-api-python-client',
        'ipdb',
        'jinja2',
        'ldap3',
        'pandas',
        'premailer',
        'progressbar2',
        'oauth2client',
    ],
    scripts=['bin/comdev'],
)


setup(**setup_info)
