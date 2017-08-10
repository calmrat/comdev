#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Chris Ward <cward@redhat.com>

'''
'''

import ipdb  # NOQA
import logging
import os
import re

import requests

from comdev import __app__
from comdev.lib import load_config, expand_path


log = logging.getLogger(__app__)


class Etherpader(object):
    pad_id = None
    cookies = None

    def __init__(self, app_name, pad_id):
        config = self.config = load_config(app_name)['etherpad'].get()
        self.url_base = self.config['url']
        self.pad_id = pad_id
        self.cookies = requests.get(self.url_base).cookies

    def create(self):
        #url = self.url_create.format(self.pad_id)
        url = self.url_create
        params = {
            'padId': self.pad_id
        }
        files = {
            'createPad': 'Yes,%20please%20create%20the%20pad',
        }
        response = requests.post(url, params=params, files=files,
                                 cookies=self.cookies)
        response.raise_for_status()

    def upload(self, path):
        path = expand_path(path)
        params = {
            'padId': self.pad_id,
        }
        files = {
            'file': open(path, 'rb'),
            'filename': path,
        }
        response = requests.post(self.url_import, params=params, files=files,
                                 cookies=self.cookies)
        response.raise_for_status()

        ######
        token = re.findall("'.+?'", response.text)[1].strip("'")
        params = {
            'padId': self.pad_id,
            'token': token,
        }
        response = requests.post(self.url_import2, params=params,
                                 cookies=self.cookies)
        response.raise_for_status()

    def readlines(self, ext='txt'):
        params = {
            'format': ext,
        }
        response = requests.post(self.url_export, params=params,
                                 cookies=self.cookies)
        content = response.text
        return content.split('\n')

    @property
    def url_export(self):
        url = os.path.join(self.url_base, 'ep/pad/export/qecamp18/latest')
        return url

    @property
    def url_pad(self):
        return os.path.join(self.url_base, self.pad_id)

    @property
    def url_create(self):
        url = os.path.join(self.url_base, 'ep/pad/create')
        return url

    @property
    def url_import(self):
        url = os.path.join(self.url_base, 'ep/pad/impexp/import')
        return url

    @property
    def url_import2(self):
        url = os.path.join(self.url_base, 'ep/pad/impexp/import2')
        return url


if __name__ == '__main__':
    e = Etherpader('qecamp', 'qecamp18')
    #e.create()
    e.upload('/tmp/out.txt')
    content = e.readlines()
    ipdb.set_trace()
