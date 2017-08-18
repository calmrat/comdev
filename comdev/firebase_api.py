#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Chris Ward <cward@redhat.com>

'''
'''

import logging

import pandas as pd
import pyrebase
import ipdb  # NOQA

from comdev.lib import load_config, expand_path


class Firebaser(object):
    _firebase_api = None

    def __init__(self, app_name):
        config = self.config = load_config(app_name)['firebase'].get()

        self.auth_conf = {
            "apiKey": config['api_key'],
            "authDomain": config['auth_domain'],
            "databaseURL": config['db_url'],
            "storageBucket": config['storage_bucket'],
            "serviceAccount": expand_path(config['service_account']),
        }

    @property
    def firebase(self):
        if not self._firebase_api:
            self._firebase_api = pyrebase.initialize_app(self.auth_conf)
        return self._firebase_api

    @property
    def db(self):
        # Get a reference to the database service
        return self.firebase.database()

    def auth_user(self, login, password=None):
        auth = self.firebase.auth()
        login = login or self.config.get('user_email')
        password = password or self.config.get('user_password')
        if login and password:
            user = auth.sign_in_with_email_and_password(login, password)
        elif login:
            # Get a reference to the auth service
            token = auth.create_custom_token(login)
            user = auth.sign_in_with_custom_token(token)
        else:
            raise ValueError(
                'Invalid user credentials. Check login and password.')
        id_token = user['idToken']
        return id_token

    def get(self, path):
        db = self.db
        child = [db.child(child_path) for child_path in path.split('.')][-1]
        # we should now be holding the correct db path reference in db var
        # grab the data
        data = child.get()
        data = {row.key(): row.val() for row in data.each()}
        df = pd.DataFrame.from_dict(data, 'index')
        return df


log = logging.getLogger(__name__)


if __name__ == '__main__':
    ipdb.set_trace()
