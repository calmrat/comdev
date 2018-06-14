#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Chris Ward <cward@redhat.com>

from setuptools import setup
import sys

from comdev import __version__ as VERSION

if sys.version_info < (3, 4):
    sys.exit('Sorry, Python < 3.4 is not supported')
    sys.exit('Python 3.6 is RECOMMENDED')

long_description = '''Community Development support library'''

# FIXME: NOTE dependency on https://wkhtmltopdf.org/downloads.html

setup_info = dict(
    # Metadata
    name='comdev',
    version=VERSION,
    license='GPLv3',
    author='Chris Ward',
    author_email='cward@redhat.com',
    description=long_description,
    long_description=long_description,
    url='https://github.com/kejbaly2/comdev',
    # Package info
    packages=['comdev'],
    install_requires=[
        'babel',
        'click',
        'confuse',
        'python-dateutil',
        #'facepy',
        #'feedparser',
        #'flask',
        # 'gdata-python3',  # py3 compatible
        'google-api-python-client',
        #'ipdb',
        #'ipython',
        'jinja2',
        #'ldap3',
        #'meetup-api',
        #'oauth2client',
        #'openpyxl',
        #'pandas',
        #'pdfkit',
        'premailer',
        'progressbar2',
        #'python-twitter',
        #'pyrebase',
        'requests',
        #'xlwt',
        # required packages for pyandoc:
        # - pandoc
        # - texlive-latex-bin-bin
        # - texlive-collection-fontsrecommended
        #'pyandoc',
    ],
    dependency_links=[
        'https://github.com/dvska/gdata-python3#egg=gdata'
        # ^^^ must run `python setup.py install` though... develop
    ],

    scripts=['bin/comdev'],
)


setup(**setup_info)
